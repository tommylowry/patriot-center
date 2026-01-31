"""Unit tests for image_urls_updater module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters.image_urls_updater import (
    update_image_urls_cache,
)


class TestUpdateImageUrlsCache:
    """Test update_image_urls_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `detect_item_type`: `mock_detect_item_type`
        - `build_url`: `mock_build_url`
        - `CACHE_MANAGER.get_image_urls_cache`: `mock_get_image_urls_cache`
        - `CACHE_MANAGER.save_image_urls_cache`: `mock_save_image_urls_cache`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.image_urls_updater"
                ".detect_item_type"
            ) as mock_detect_item_type,
            patch(
                "patriot_center_backend.cache.updaters.image_urls_updater"
                ".build_url"
            ) as mock_build_url,
            patch(
                "patriot_center_backend.cache.updaters.image_urls_updater"
                ".CACHE_MANAGER.get_image_urls_cache"
            ) as mock_get_image_urls_cache,
            patch(
                "patriot_center_backend.cache.updaters.image_urls_updater"
                ".CACHE_MANAGER.save_image_urls_cache"
            ) as mock_save_image_urls_cache,
        ):
            self.mock_detect_item_type = mock_detect_item_type
            self.mock_build_url = mock_build_url
            self.mock_image_urls_cache = {}
            mock_get_image_urls_cache.return_value = self.mock_image_urls_cache
            self.mock_save_image_urls_cache = mock_save_image_urls_cache

            yield

    def test_stores_url_dict_in_cache(self):
        """Test stores the URL dict in the image URLs cache."""
        self.mock_detect_item_type.return_value = "player"
        self.mock_build_url.return_value = {
            "name": "Patrick Mahomes",
            "image_url": "https://sleepercdn.com/content/nfl/players/4046.jpg",
        }

        update_image_urls_cache("Patrick Mahomes")

        assert self.mock_image_urls_cache["Patrick Mahomes"] == {
            "name": "Patrick Mahomes",
            "image_url": "https://sleepercdn.com/content/nfl/players/4046.jpg",
        }

    def test_saves_cache_for_manager_type(self):
        """Test saves image URLs cache when item type is manager."""
        self.mock_detect_item_type.return_value = "manager"
        self.mock_build_url.return_value = {
            "name": "Tommy",
            "image_url": "https://sleepercdn.com/avatars/abc123",
        }

        update_image_urls_cache("Tommy")

        self.mock_save_image_urls_cache.assert_called_once()

    def test_does_not_save_cache_for_non_manager_type(self):
        """Test does not save image URLs cache for non-manager types."""
        self.mock_detect_item_type.return_value = "player"
        self.mock_build_url.return_value = {"name": "Patrick Mahomes"}

        update_image_urls_cache("Patrick Mahomes")

        self.mock_save_image_urls_cache.assert_not_called()

    def test_returns_url_dict(self):
        """Test returns the URL dict from build_url."""
        self.mock_detect_item_type.return_value = "draft_pick"
        expected = {"name": "Tommy's 2024 Round 1 Draft Pick"}
        self.mock_build_url.return_value = expected

        result = update_image_urls_cache("Tommy's 2024 Round 1 Draft Pick")

        assert result == expected

    def test_passes_correct_args_to_build_url(self):
        """Test passes correct item and item_type to build_url."""
        self.mock_detect_item_type.return_value = "faab"
        self.mock_build_url.return_value = {}

        update_image_urls_cache("$10 FAAB")

        self.mock_build_url.assert_called_once_with("$10 FAAB", "faab")
