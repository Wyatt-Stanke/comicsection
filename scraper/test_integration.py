"""Integration tests for the comic scraper.

These tests verify the scraper works end-to-end by deleting the comics
folder and running the actual scraper to see if it can download all
comics without problems. This exercises the real browser-based scraping
path (Selenium + headless Chrome) instead of plain HTTP requests, which
don't work because GoComics is behind a JS challenge.
"""

import os
import shutil
import subprocess
import sys

import pytest

# The comics directory is one level up from the scraper directory
SCRAPER_DIR = os.path.dirname(os.path.abspath(__file__))
COMICS_DIR = os.path.join(SCRAPER_DIR, "..", "comics")


def network_available():
    """Check if network is available by trying to reach a known host."""
    try:
        import requests
        requests.get("https://www.google.com", timeout=5)
        return True
    except (ImportError, requests.exceptions.RequestException):
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
    def test_scraper_downloads_comics(self):
        """Delete the comics folder, run the scraper, and verify files were downloaded."""
        # Step 1: Delete the comics folder
        force_remove_dir(COMICS_DIR)
        assert not os.path.exists(COMICS_DIR)

        # Step 2: Run the scraper
        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=SCRAPER_DIR,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout for all comics (12 comics × 7 days)
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        assert result.returncode == 0, (
            f"Scraper failed with return code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # Step 3: Verify the comics folder was created with content
        assert os.path.exists(COMICS_DIR), "Comics directory was not created"

        comic_dirs = [
            d for d in os.listdir(COMICS_DIR)
            if os.path.isdir(os.path.join(COMICS_DIR, d))
        ]
        assert len(comic_dirs) > 0, "No comic directories were created"

        # Step 4: Verify each comic directory has downloaded files or placeholders
        for comic in comic_dirs:
            comic_dir = os.path.join(COMICS_DIR, comic)
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
