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

# Get chrome version without launching a full browser, try chromedriver --version as well as google-chrome --version
# error if both fail
def get_chrome_version():
    try:
        result = subprocess.run(
            ["chromedriver", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        version_str = result.stdout.strip().split(" ")[1]
        return version_str
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["google-chrome", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        version_str = result.stdout.strip().split(" ")[2]
        return version_str
    except Exception:
        pass

    raise RuntimeError("Could not determine Chrome version")