"""Integration tests for the comic scraper.

These tests verify the scraper works end-to-end by running the actual
scraper against a small subset of comics into a temporary directory.
This exercises the real browser-based scraping path (Selenium + headless
Chrome) instead of plain HTTP requests, which don't work because
GoComics is behind a JS challenge.
"""

import os
import shutil
import subprocess
import sys

import pytest

SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))

# Test configuration: small subset to keep CI fast
TEST_COMICS = "garfield"
TEST_DAYS = "1"


def network_available():
    """Check if network is available by trying to reach a known host."""
    try:
        import requests
        requests.get("https://www.google.com", timeout=5)
        return True
    except ImportError:
        return False
    except requests.exceptions.RequestException:
        return False


def force_remove_dir(path):
    """Remove a directory tree. Tries rm -rf first, falls back to shutil."""
    if not os.path.exists(path):
        return
    try:
        subprocess.run(["rm", "-rf", path], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        shutil.rmtree(path)


requires_network = pytest.mark.skipif(
    not network_available(),
    reason="Network not available"
)


class TestScraperIntegration:
    """Integration test that runs the actual scraper end-to-end."""

    @requires_network
    def test_scraper_downloads_comics(self, tmp_path):
        """Run the scraper into a temp directory and verify files were downloaded."""
        output_dir = str(tmp_path)
        comics_dir = os.path.join(output_dir, "comics")

        # Run the scraper with a small subset, outputting to the temp directory
        env = os.environ.copy()
        env["SCRAPER_COMICS"] = TEST_COMICS
        env["SCRAPER_DAYS"] = TEST_DAYS
        env["SCRAPER_BASE_DIR"] = output_dir

        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=SCRAPER_DIR,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout for a single comic/day
            env=env,
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        assert result.returncode == 0, (
            f"Scraper failed with return code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # Verify the comics folder was created with content
        assert os.path.exists(comics_dir), "Comics directory was not created"

        comic_dirs = [
            d for d in os.listdir(comics_dir)
            if os.path.isdir(os.path.join(comics_dir, d))
        ]
        assert len(comic_dirs) > 0, "No comic directories were created"

        # Verify each comic directory has downloaded files or placeholders
        for comic in comic_dirs:
            comic_dir = os.path.join(comics_dir, comic)
            date_dirs = [
                d for d in os.listdir(comic_dir)
                if os.path.isdir(os.path.join(comic_dir, d))
            ]
            assert len(date_dirs) > 0, (
                f"No date directories found for comic '{comic}'"
            )

            has_content = False
            for date_dir in date_dirs:
                full_date_dir = os.path.join(comic_dir, date_dir)
                files = os.listdir(full_date_dir)
                if "comic.webp" in files or ".placeholder" in files:
                    has_content = True
                    break

            assert has_content, (
                f"No comic.webp or .placeholder found for comic '{comic}'"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
