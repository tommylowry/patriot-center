"""Unit tests for image_url_handler module."""

import logging
from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.utils.image_url_handler import (
    _handle_if_manager,
    get_image_url,
)

MODULE_PATH = "patriot_center_backend.utils.image_url_handler"


class TestGetImageUrl:
    """Test get_image_url function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `detect_item_type`: `mock_detect_item_type`
        - `CACHE_MANAGER.get_image_urls_cache`:
            `mock_get_image_urls_cache`
        - `update_image_urls_cache`:
            `mock_update_image_urls_cache`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.detect_item_type"
            ) as mock_detect_item_type,
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_image_urls_cache"
            ) as mock_get_image_urls_cache,
            patch(
                f"{MODULE_PATH}.update_image_urls_cache"
            ) as mock_update_image_urls_cache,
        ):
            self.mock_detect_item_type = mock_detect_item_type
            self.mock_detect_item_type.return_value = "player"

            self.mock_image_urls_cache: dict[str, Any] = {
                "Patrick Mahomes": {
                    "image_url": "https://example.com/mahomes.jpg",
                    "name": "Patrick Mahomes",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                },
            }
            mock_get_image_urls_cache.return_value = (
                self.mock_image_urls_cache
            )

            self.mock_update_image_urls_cache = mock_update_image_urls_cache
            self.mock_update_image_urls_cache.return_value = {
                "image_url": "https://example.com/new.jpg",
                "name": "New Player",
            }

            yield

    def test_returns_empty_string_for_unknown_item(self):
        """Test returns empty string for unknown item type."""
        self.mock_detect_item_type.return_value = "unknown"

        result = get_image_url("???")

        assert result == ""

    def test_returns_empty_dict_for_unknown_item_with_dictionary(self):
        """Test returns empty dict for unknown item with dictionary=True."""
        self.mock_detect_item_type.return_value = "unknown"

        result = get_image_url("???", dictionary=True)

        assert result == {}

    def test_returns_url_string_for_cached_player(self):
        """Test returns URL string for player found in cache."""
        result = get_image_url("Patrick Mahomes")

        assert result == "https://example.com/mahomes.jpg"

    def test_returns_dict_for_cached_player_with_dictionary(self):
        """Test returns dict for player found in cache with dictionary=True."""
        result = get_image_url("Patrick Mahomes", dictionary=True)

        assert (
            result["image_url"]  # type: ignore
            == "https://example.com/mahomes.jpg"
        )

    def test_fetches_and_returns_url_for_uncached_item(self):
        """Test fetches URL when item not in cache."""
        result = get_image_url("Jayden Daniels")

        self.mock_update_image_urls_cache.assert_called_once_with(
            "Jayden Daniels"
        )
        assert result == "https://example.com/new.jpg"

    def test_fetches_and_returns_dict_for_uncached_item_with_dictionary(self):
        """Test fetches dict when item not in cache with dictionary=True."""
        result = get_image_url("Jayden Daniels", dictionary=True)

        assert (
            result["image_url"]  # type: ignore
            == "https://example.com/new.jpg"
        )

    def test_delegates_to_handle_if_manager_for_manager_type(self):
        """Test delegates to _handle_if_manager for manager type."""
        self.mock_detect_item_type.return_value = "manager"
        self.mock_image_urls_cache["Tommy"] = {
            "image_url": "https://example.com/tommy.jpg",
            "name": "Tommy",
            "timestamp": "9999999999",
        }

        result = get_image_url("Tommy")

        assert result == "https://example.com/tommy.jpg"

    def test_logs_warning_for_unknown_type(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test logs warning for unknown item type.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_detect_item_type.return_value = "unknown"

        with caplog.at_level(logging.WARNING):
            get_image_url("???")

        assert "Could not find image URL" in caplog.text


class TestHandleIfManager:
    """Test _handle_if_manager function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `update_image_urls_cache`:
            `mock_update_image_urls_cache`

        Yields:
            None
        """
        with patch(
            f"{MODULE_PATH}.update_image_urls_cache"
        ) as mock_update_image_urls_cache:
            self.mock_update_image_urls_cache = mock_update_image_urls_cache
            self.mock_update_image_urls_cache.return_value = {
                "image_url": "https://example.com/fresh.jpg",
                "name": "Tommy",
                "timestamp": "9999999999",
            }

            yield

    def test_returns_url_string_when_timestamp_fresh(self):
        """Test returns URL string when timestamp is fresh (< 1 hour)."""
        manager_entry = {
            "image_url": "https://example.com/tommy.jpg",
            "name": "Tommy",
            "timestamp": "9999999999",
        }

        result = _handle_if_manager(manager_entry, dictionary=False)

        assert result == "https://example.com/tommy.jpg"
        self.mock_update_image_urls_cache.assert_not_called()

    def test_returns_dict_when_timestamp_fresh(self):
        """Test returns dict when timestamp is fresh with dictionary=True."""
        manager_entry = {
            "image_url": "https://example.com/tommy.jpg",
            "name": "Tommy",
            "timestamp": "9999999999",
        }

        result = _handle_if_manager(manager_entry, dictionary=True)

        assert (
            result["image_url"]  # type: ignore
            == "https://example.com/tommy.jpg"
        )

    def test_refreshes_when_timestamp_stale(self):
        """Test refreshes URL when timestamp is stale (> 1 hour)."""
        manager_entry = {
            "image_url": "https://example.com/old.jpg",
            "name": "Tommy",
            "timestamp": "0",
        }

        result = _handle_if_manager(manager_entry, dictionary=False)

        self.mock_update_image_urls_cache.assert_called_once_with("Tommy")
        assert result == "https://example.com/fresh.jpg"

    def test_refreshes_when_no_timestamp(self):
        """Test refreshes URL when no timestamp present."""
        manager_entry = {
            "image_url": "https://example.com/old.jpg",
            "name": "Tommy",
        }

        _handle_if_manager(manager_entry, dictionary=False)

        self.mock_update_image_urls_cache.assert_called_once_with("Tommy")

    def test_removes_timestamp_from_dict_return(self):
        """Test removes timestamp key from returned dict."""
        manager_entry = {
            "image_url": "https://example.com/old.jpg",
            "name": "Tommy",
            "timestamp": "0",
        }

        result = _handle_if_manager(manager_entry, dictionary=True)

        assert "timestamp" not in result
