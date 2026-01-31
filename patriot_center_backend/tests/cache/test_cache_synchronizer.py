"""Unit tests for cache_synchronizer module."""

import logging
from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.cache_synchronizer import CacheSynchronizer


class TestSynchronize:
    """Test CacheSynchronizer.synchronize method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`: `mock_get_player_ids`
        - `CACHE_MANAGER.save_all_caches`: `mock_save_all_caches`
        - `CacheSynchronizer._update_player_names`:
            `mock_update_player_names`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids,
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".CACHE_MANAGER.save_all_caches"
            ) as mock_save_all_caches,
        ):
            self.mock_old_ids: dict[str, dict[str, Any]] = {
                "4046": {
                    "full_name": "Patrick Mahomes",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                },
                "6794": {
                    "full_name": "Jayden Daniels",
                    "first_name": "Jayden",
                    "last_name": "Daniels",
                },
            }
            mock_get_player_ids.return_value = self.mock_old_ids
            self.mock_save_all_caches = mock_save_all_caches

            yield

    def test_no_name_changes_does_not_update(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test no updates when names have not changed.

        Args:
            caplog: pytest caplog fixture
        """
        new_ids = {
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
            },
            "6794": {
                "full_name": "Jayden Daniels",
                "first_name": "Jayden",
                "last_name": "Daniels",
            },
        }

        with patch.object(
            CacheSynchronizer, "_update_player_names"
        ) as mock_update:
            synchronizer = CacheSynchronizer(new_ids)
            synchronizer.synchronize()

            mock_update.assert_not_called()

    def test_detects_name_change_and_calls_update(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test detects name change and calls _update_player_names.

        Args:
            caplog: pytest caplog fixture
        """
        new_ids = {
            "4046": {
                "full_name": "Patrick Mahomes II",
                "first_name": "Patrick",
                "last_name": "Mahomes II",
            },
            "6794": {
                "full_name": "Jayden Daniels",
                "first_name": "Jayden",
                "last_name": "Daniels",
            },
        }

        with patch.object(
            CacheSynchronizer, "_update_player_names"
        ) as mock_update:
            with caplog.at_level(logging.INFO):
                synchronizer = CacheSynchronizer(new_ids)
                synchronizer.synchronize()

            mock_update.assert_called_once_with("4046")

    def test_saves_all_caches_after_synchronize(self):
        """Test saves all caches after synchronization."""
        new_ids = {
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
            },
            "6794": {
                "full_name": "Jayden Daniels",
                "first_name": "Jayden",
                "last_name": "Daniels",
            },
        }

        with patch.object(CacheSynchronizer, "_update_player_names"):
            synchronizer = CacheSynchronizer(new_ids)
            synchronizer.synchronize()

        self.mock_save_all_caches.assert_called_once()


class TestUpdatePlayerNames:
    """Test CacheSynchronizer._update_player_names method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`: `mock_get_player_ids`
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `CACHE_MANAGER.get_player_data_cache`:
            `mock_get_player_data_cache`
        - `CACHE_MANAGER.get_starters_cache`: `mock_get_starters_cache`
        - `CACHE_MANAGER.get_transaction_ids_cache`:
            `mock_get_transaction_ids`
        - `CACHE_MANAGER.get_valid_options_cache`:
            `mock_get_valid_options`
        - `CACHE_MANAGER.get_players_cache`: `mock_get_players_cache`
        - `CACHE_MANAGER.get_image_urls_cache`:
            `mock_get_image_urls_cache`
        - `CACHE_MANAGER.save_all_caches`: `mock_save_all_caches`
        - `recursive_replace`: `mock_recursive_replace`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids,
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".CACHE_MANAGER.get_player_data_cache"
            ) as mock_get_player_data_cache,
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".CACHE_MANAGER.get_starters_cache"
            ) as mock_get_starters_cache,
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".CACHE_MANAGER.get_transaction_ids_cache"
            ) as mock_get_transaction_ids,
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options,
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".CACHE_MANAGER.get_players_cache"
            ) as mock_get_players_cache,
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".CACHE_MANAGER.get_image_urls_cache"
            ) as mock_get_image_urls_cache,
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".CACHE_MANAGER.save_all_caches"
            ),
            patch(
                "patriot_center_backend.cache.cache_synchronizer"
                ".recursive_replace"
            ) as mock_recursive_replace,
        ):
            self.mock_old_ids = {
                "4046": {
                    "full_name": "Pat Mahomes",
                    "first_name": "Pat",
                    "last_name": "Mahomes",
                },
            }
            mock_get_player_ids.return_value = self.mock_old_ids

            mock_get_manager_cache.return_value = {}
            mock_get_player_data_cache.return_value = {}
            mock_get_starters_cache.return_value = {}
            mock_get_transaction_ids.return_value = {}
            mock_get_valid_options.return_value = {}
            mock_get_players_cache.return_value = {}

            self.mock_image_urls_cache: dict[str, Any] = {}
            mock_get_image_urls_cache.return_value = self.mock_image_urls_cache

            self.mock_recursive_replace = mock_recursive_replace
            self.mock_recursive_replace.side_effect = lambda data, old, new: (
                data
            )

            yield

    def test_calls_recursive_replace_for_all_caches(self):
        """Test calls recursive_replace for all 6 caches."""
        new_ids = {
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
            },
        }

        synchronizer = CacheSynchronizer(new_ids)
        synchronizer._update_player_names("4046")

        assert self.mock_recursive_replace.call_count == 6

    def test_updates_image_urls_cache_by_player_id(self):
        """Test updates image URLs cache entry by player_id."""
        self.mock_image_urls_cache["4046"] = {
            "name": "Pat Mahomes",
            "first_name": "Pat",
            "last_name": "Mahomes",
        }

        new_ids = {
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
            },
        }

        synchronizer = CacheSynchronizer(new_ids)
        synchronizer._update_player_names("4046")

        assert self.mock_image_urls_cache["4046"]["name"] == ("Patrick Mahomes")
        assert self.mock_image_urls_cache["4046"]["first_name"] == "Patrick"

    def test_updates_image_urls_cache_by_full_name(self):
        """Test renames image URLs cache key from old name to new name."""
        self.mock_image_urls_cache["Pat Mahomes"] = {
            "image_url": "https://example.com/pat.jpg",
            "name": "Pat Mahomes",
            "first_name": "Pat",
            "last_name": "Mahomes",
        }

        new_ids = {
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
            },
        }

        synchronizer = CacheSynchronizer(new_ids)
        synchronizer._update_player_names("4046")

        assert "Pat Mahomes" not in self.mock_image_urls_cache
        assert "Patrick Mahomes" in self.mock_image_urls_cache
        assert self.mock_image_urls_cache["Patrick Mahomes"]["image_url"] == (
            "https://example.com/pat.jpg"
        )
