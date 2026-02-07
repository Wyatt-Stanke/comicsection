"""Utility functions for the comic scraper."""

import os
from datetime import date
import subprocess

def get_image_path(comic_name: str, comic_date: date, base_dir: str = "..") -> str:
    """Generate the path for storing a comic image.

    Args:
        comic_name: The name/id of the comic
        comic_date: The date of the comic
        base_dir: Base directory for comics storage

    Returns:
        The full path where the comic image should be stored
    """
    return os.path.join(
        base_dir, "comics", comic_name, comic_date.strftime("%Y-%m-%d"), "comic.webp"
    )


def get_placeholder_path(comic_name: str, comic_date: date, base_dir: str = "..") -> str:
    """Generate the path for a placeholder file.

    Args:
        comic_name: The name/id of the comic
        comic_date: The date of the comic
        base_dir: Base directory for comics storage

    Returns:
        The full path where the placeholder file should be stored
    """
    return os.path.join(
        base_dir, "comics", comic_name, comic_date.strftime("%Y-%m-%d"), ".placeholder"
    )


def build_gocomics_url(comic: str, comic_date: date) -> str:
    """Build a GoComics URL for a specific comic and date.

    Args:
        comic: The comic slug/id
        comic_date: The date to fetch

    Returns:
        The full GoComics URL
    """
    return (
        f"https://www.gocomics.com/"
        f"{comic}/{comic_date.year}/{comic_date.month}/{comic_date.day}"
    )


def is_valid_comic_name(comic_name: str) -> bool:
    """Check if a comic name is valid (non-empty, ASCII alphanumeric with optional hyphens).

    Args:
        comic_name: The comic name to validate

    Returns:
        True if valid, False otherwise
    """
    if not comic_name or not isinstance(comic_name, str):
        return False
    return all(c.isascii() and (c.isalnum() or c == '-') for c in comic_name)

# Get Chrome version without launching a full browser.
# Prefer the actual browser binary (google-chrome) and only fall back to chromedriver.
# When using chromedriver, normalize to the major version to reduce mismatch issues.
def get_chrome_version():
    # First, try the installed Google Chrome browser.
    try:
        result = subprocess.run(
            ["google-chrome", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Typical output: "Google Chrome 120.0.6099.109"
        parts = result.stdout.strip().split(" ")
        if len(parts) >= 3:
            version_str = parts[2]
            return version_str
    except Exception:
        pass

    # Fallback: use chromedriver version, but only return the major version.
    try:
        result = subprocess.run(
            ["chromedriver", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Typical output: "ChromeDriver 120.0.6099.109 (..."
        parts = result.stdout.strip().split(" ")
        if len(parts) >= 2:
            full_version = parts[1]
            major_version = full_version.split(".")[0]
            if major_version.isdigit():
                return major_version
    except Exception:
        pass

    raise RuntimeError("Could not determine Chrome version")