"""Integration tests for the comic scraper.

These tests verify that multiple components work together and that
external services are reachable. They make actual network requests.

Tests marked with @pytest.mark.network require network access and will
be skipped in environments without internet connectivity.
"""

import os
import time
from datetime import date, timedelta
from io import BytesIO

import pytest
import requests
from PIL import Image

from utils import build_gocomics_url, get_image_path, is_valid_comic_name


def request_with_backoff(
    url: str,
    timeout: int = 30,
    max_retries: int = 5,
    base_delay: float = 1.0,
) -> requests.Response:
    """Make an HTTP GET request with exponential backoff for 403 errors.

    Args:
        url: The URL to request
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles with each retry)

    Returns:
        The response object

    Raises:
        requests.exceptions.HTTPError: If all retries are exhausted for 403 errors
        requests.exceptions.RequestException: For other request failures after max retries
    """
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 403:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise

    # This line should never be reached since the loop always either returns or raises
    raise requests.exceptions.HTTPError("Max retries exceeded")


def network_available():
    """Check if network is available by trying to reach a known host."""
    try:
        request_with_backoff("https://www.google.com", timeout=5, max_retries=2, base_delay=0.5)
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError):
        return False


# Skip decorator for network tests
requires_network = pytest.mark.skipif(
    not network_available(),
    reason="Network not available"
)


class TestGoComicsIntegration:
    """Integration tests for GoComics fetching."""

    @pytest.fixture
    def known_comic_date(self):
        """Return a date that we know has comics available."""
        # Use a date from the past that we know has comics
        return date(2024, 1, 15)

    @requires_network
    def test_gocomics_url_is_reachable(self, known_comic_date):
        """Test that GoComics URLs return a valid response."""
        url = build_gocomics_url("garfield", known_comic_date)
        response = request_with_backoff(url, timeout=30)
        assert response.status_code == 200
        assert "gocomics.com" in response.url

    @requires_network
    def test_gocomics_page_contains_comic_image(self, known_comic_date):
        """Test that the GoComics page contains an image element."""
        url = build_gocomics_url("garfield", known_comic_date)
        response = request_with_backoff(url, timeout=30)
        # Check that the page contains image-related content
        assert response.status_code == 200
        # The page should contain img tags or comic-related content
        assert "<img" in response.text or "comic" in response.text.lower()

    @requires_network
    def test_multiple_comics_are_reachable(self, known_comic_date):
        """Test that multiple known comics are reachable."""
        comics = ["garfield", "bignate", "calvinandhobbes"]
        for comic in comics:
            url = build_gocomics_url(comic, known_comic_date)
            response = request_with_backoff(url, timeout=30)
            assert response.status_code == 200, f"Failed to reach {comic}"


class TestImageDownloadIntegration:
    """Integration tests for image downloading."""

    @requires_network
    def test_can_download_and_parse_image(self):
        """Test downloading and parsing an image from a known URL."""
        # Use a stable, publicly available test image
        test_url = "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
        response = request_with_backoff(test_url, timeout=30)
        assert response.status_code == 200

        # Verify we can parse it as an image
        image = Image.open(BytesIO(response.content))
        assert image is not None
        assert image.size[0] > 0
        assert image.size[1] > 0

    def test_can_parse_image_from_bytes(self):
        """Test that PIL can parse image data from bytes (offline test)."""
        # Create a simple PNG image in memory
        img = Image.new('RGB', (10, 10), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Parse it back
        parsed = Image.open(buffer)
        assert parsed.size == (10, 10)


class TestPathAndUrlWorkflow:
    """Integration tests for path generation and URL building workflow."""

    def test_full_workflow_path_generation(self):
        """Test the complete workflow of validating, building URL, and generating path."""
        comic_name = "garfield"
        comic_date = date(2024, 6, 15)

        # Step 1: Validate comic name
        assert is_valid_comic_name(comic_name) is True

        # Step 2: Build URL
        url = build_gocomics_url(comic_name, comic_date)
        assert "garfield" in url
        assert "2024" in url

        # Step 3: Generate storage path
        path = get_image_path(comic_name, comic_date)
        assert comic_name in path
        assert "2024-06-15" in path
        assert path.endswith("comic.webp")

    def test_workflow_with_multiple_dates(self):
        """Test workflow with multiple consecutive dates (like the scraper does)."""
        comic_name = "bignate"
        days_past = 3

        paths = []
        urls = []

        for i in range(days_past):
            comic_date = date.today() - timedelta(days=i)

            # Validate
            assert is_valid_comic_name(comic_name)

            # Build URL
            url = build_gocomics_url(comic_name, comic_date)
            urls.append(url)

            # Generate path
            path = get_image_path(comic_name, comic_date)
            paths.append(path)

        # All paths should be unique
        assert len(set(paths)) == days_past

        # All URLs should be unique
        assert len(set(urls)) == days_past

    def test_workflow_rejects_invalid_comic(self):
        """Test that the workflow correctly rejects invalid comic names."""
        invalid_names = ["", None, "comic with spaces", "comic@special"]

        for name in invalid_names:
            assert is_valid_comic_name(name) is False


class TestEndToEndScenarios:
    """End-to-end test scenarios simulating actual usage."""

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create a temporary directory for test outputs."""
        output_dir = tmp_path / "comics"
        output_dir.mkdir()
        return str(output_dir)

    @requires_network
    def test_complete_comic_fetch_scenario(self, temp_output_dir):
        """Test a complete scenario: validate -> build URL -> fetch page -> verify."""
        comic_name = "garfield"
        comic_date = date(2024, 1, 15)

        # Step 1: Validate the comic name
        assert is_valid_comic_name(comic_name)

        # Step 2: Generate the storage path
        image_path = get_image_path(comic_name, comic_date, base_dir=temp_output_dir)
        assert temp_output_dir in image_path

        # Step 3: Build the URL
        url = build_gocomics_url(comic_name, comic_date)

        # Step 4: Verify URL is reachable
        response = request_with_backoff(url, timeout=30)
        assert response.status_code == 200

        # Step 5: Verify we can create the directory structure
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        assert os.path.exists(os.path.dirname(image_path))

    @requires_network
    def test_multiple_comics_scrape_scenario(self, temp_output_dir):
        """Test scraping multiple comics like the actual scraper does."""
        comics = ["garfield", "bignate"]
        comic_date = date(2024, 1, 15)

        results = []

        for comic in comics:
            # Validate
            if not is_valid_comic_name(comic):
                continue

            # Build URL and path
            url = build_gocomics_url(comic, comic_date)
            path = get_image_path(comic, comic_date, base_dir=temp_output_dir)

            # Fetch page
            response = request_with_backoff(url, timeout=30)

            results.append({
                "comic": comic,
                "url": url,
                "path": path,
                "status": response.status_code,
            })

        # All comics should be successfully fetched
        assert len(results) == len(comics)
        for result in results:
            assert result["status"] == 200

    def test_complete_workflow_without_network(self, temp_output_dir):
        """Test the complete workflow without making network requests."""
        comic_name = "garfield"
        comic_date = date(2024, 1, 15)

        # Step 1: Validate the comic name
        assert is_valid_comic_name(comic_name)

        # Step 2: Generate the storage path
        image_path = get_image_path(comic_name, comic_date, base_dir=temp_output_dir)
        assert temp_output_dir in image_path
        assert comic_name in image_path
        assert "2024-01-15" in image_path

        # Step 3: Build the URL
        url = build_gocomics_url(comic_name, comic_date)
        assert "gocomics.com" in url
        assert comic_name in url

        # Step 4: Verify we can create the directory structure
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        assert os.path.exists(os.path.dirname(image_path))

        # Step 5: Simulate saving an image
        img = Image.new('RGB', (100, 100), color='white')
        img.save(image_path.replace('.webp', '.png'), format='PNG')
        assert os.path.exists(image_path.replace('.webp', '.png'))

    def test_batch_processing_workflow(self, temp_output_dir):
        """Test processing multiple comics over multiple days (offline)."""
        comics = ["garfield", "bignate", "calvinandhobbes"]
        days = 3

        processed = []

        for comic in comics:
            if not is_valid_comic_name(comic):
                continue

            for i in range(days):
                comic_date = date(2024, 1, 15) - timedelta(days=i)

                url = build_gocomics_url(comic, comic_date)
                path = get_image_path(comic, comic_date, base_dir=temp_output_dir)

                # Create directory
                os.makedirs(os.path.dirname(path), exist_ok=True)

                processed.append({
                    "comic": comic,
                    "date": comic_date,
                    "url": url,
                    "path": path,
                })

        # Should have processed comics * days entries
        assert len(processed) == len(comics) * days

        # All URLs should be unique
        urls = [p["url"] for p in processed]
        assert len(set(urls)) == len(urls)

        # All paths should be unique
        paths = [p["path"] for p in processed]
        assert len(set(paths)) == len(paths)


class TestRequestWithBackoff:
    """Tests for the request_with_backoff helper function."""

    def test_successful_request_returns_immediately(self, requests_mock):
        """Test that a successful request returns immediately without retries."""
        test_url = "https://example.com/api"
        requests_mock.get(test_url, text="OK", status_code=200)

        response = request_with_backoff(test_url, timeout=5, max_retries=3, base_delay=0.01)
        assert response.status_code == 200
        assert response.text == "OK"
        assert requests_mock.call_count == 1

    def test_retries_on_403_error(self, requests_mock):
        """Test that 403 errors trigger retries."""
        test_url = "https://example.com/api"
        # First two requests return 403, third succeeds
        requests_mock.get(
            test_url,
            [
                {"status_code": 403},
                {"status_code": 403},
                {"text": "OK", "status_code": 200},
            ],
        )

        response = request_with_backoff(test_url, timeout=5, max_retries=3, base_delay=0.01)
        assert response.status_code == 200
        assert requests_mock.call_count == 3

    def test_raises_on_max_retries_exceeded(self, requests_mock):
        """Test that HTTPError is raised when max retries are exhausted."""
        test_url = "https://example.com/api"
        requests_mock.get(test_url, status_code=403)

        with pytest.raises(requests.exceptions.HTTPError):
            request_with_backoff(test_url, timeout=5, max_retries=2, base_delay=0.01)

        # Should have tried 3 times (initial + 2 retries)
        assert requests_mock.call_count == 3

    def test_non_403_errors_return_immediately(self, requests_mock):
        """Test that non-403 status codes don't trigger retries."""
        test_url = "https://example.com/api"
        requests_mock.get(test_url, status_code=404)

        response = request_with_backoff(test_url, timeout=5, max_retries=3, base_delay=0.01)
        assert response.status_code == 404
        assert requests_mock.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
