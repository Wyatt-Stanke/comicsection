"""Tests for the comic scraper utility functions."""

import os
from datetime import date

import pytest

from utils import (
    get_image_path,
    get_placeholder_path,
    build_gocomics_url,
    is_valid_comic_name,
)


class TestGetImagePath:
    """Tests for get_image_path function."""

    def test_basic_path_generation(self):
        """Test basic path generation for a comic."""
        comic_date = date(2024, 1, 15)
        result = get_image_path("garfield", comic_date)
        expected = os.path.join("..", "comics", "garfield", "2024-01-15", "comic.webp")
        assert result == expected

    def test_custom_base_directory(self):
        """Test path generation with custom base directory."""
        comic_date = date(2024, 6, 30)
        result = get_image_path("bignate", comic_date, base_dir="/custom/path")
        expected = os.path.join("/custom/path", "comics", "bignate", "2024-06-30", "comic.webp")
        assert result == expected

    def test_date_formatting(self):
        """Test that dates are formatted correctly with zero padding."""
        comic_date = date(2024, 1, 5)
        result = get_image_path("comic", comic_date)
        assert "2024-01-05" in result


class TestGetPlaceholderPath:
    """Tests for get_placeholder_path function."""

    def test_basic_placeholder_path(self):
        """Test basic placeholder path generation."""
        comic_date = date(2024, 3, 20)
        result = get_placeholder_path("calvinandhobbes", comic_date)
        expected = os.path.join("..", "comics", "calvinandhobbes", "2024-03-20", ".placeholder")
        assert result == expected

    def test_custom_base_directory(self):
        """Test placeholder path with custom base directory."""
        comic_date = date(2024, 12, 31)
        result = get_placeholder_path("foxtrot", comic_date, base_dir="./output")
        expected = os.path.join("./output", "comics", "foxtrot", "2024-12-31", ".placeholder")
        assert result == expected


class TestBuildGocomicsUrl:
    """Tests for build_gocomics_url function."""

    def test_basic_url_construction(self):
        """Test basic URL construction."""
        comic_date = date(2024, 5, 15)
        result = build_gocomics_url("garfield", comic_date)
        assert result == "https://www.gocomics.com/garfield/2024/5/15"

    def test_url_with_different_comic(self):
        """Test URL construction with different comic names."""
        comic_date = date(2024, 1, 1)
        result = build_gocomics_url("pearlsbeforeswine", comic_date)
        assert result == "https://www.gocomics.com/pearlsbeforeswine/2024/1/1"

    def test_url_date_components(self):
        """Test that date components are correctly included."""
        comic_date = date(2023, 12, 25)
        result = build_gocomics_url("bignate", comic_date)
        assert "/2023/" in result
        assert "/12/" in result
        assert "/25" in result


class TestIsValidComicName:
    """Tests for is_valid_comic_name function."""

    def test_valid_alphanumeric_name(self):
        """Test valid alphanumeric comic names."""
        assert is_valid_comic_name("garfield") is True
        assert is_valid_comic_name("bignate") is True
        assert is_valid_comic_name("calvinandhobbes") is True

    def test_valid_name_with_hyphen(self):
        """Test valid names with hyphens."""
        assert is_valid_comic_name("calvin-and-hobbes") is True

    def test_empty_name(self):
        """Test that empty names are invalid."""
        assert is_valid_comic_name("") is False

    def test_none_name(self):
        """Test that None names are invalid (returns False, not exception)."""
        result = is_valid_comic_name(None)
        assert result is False

    def test_name_with_numbers(self):
        """Test valid names with numbers."""
        assert is_valid_comic_name("comic123") is True
        assert is_valid_comic_name("123comic") is True

    def test_invalid_input_types(self):
        """Test that non-string types are invalid."""
        assert is_valid_comic_name(123) is False
        assert is_valid_comic_name([]) is False
        assert is_valid_comic_name(True) is False
        assert is_valid_comic_name({}) is False

    def test_invalid_characters(self):
        """Test that URL-unsafe and special characters are rejected."""
        assert is_valid_comic_name("comic with spaces") is False
        assert is_valid_comic_name("comic@special") is False
        assert is_valid_comic_name("comic/with/slash") is False
        assert is_valid_comic_name("comic.with.dot") is False
        assert is_valid_comic_name("comic%with%percent") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
