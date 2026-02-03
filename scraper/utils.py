"""Utility functions for the comic scraper."""

import os
from datetime import date


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
    year = comic_date.year
    month = comic_date.month
    day = comic_date.day
    return f"https://www.gocomics.com/{comic}/{year}/{month}/{day}"


def is_valid_comic_name(comic_name: str) -> bool:
    """Check if a comic name is valid (non-empty, alphanumeric with optional hyphens).

    Args:
        comic_name: The comic name to validate

    Returns:
        True if valid, False otherwise
    """
    if not comic_name or not isinstance(comic_name, str):
        return False
    return all(c.isalnum() or c == '-' for c in comic_name)
