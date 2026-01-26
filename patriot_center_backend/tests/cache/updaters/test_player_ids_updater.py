"""Unit tests for player_ids_updater module."""

import logging
from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters.player_ids_updater import (
    _recursive_replace,
    _update_new_names,
    update_player_ids_cache,
)


class TestUpdatePlayerIdsCache:
    """Test update_player_ids_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`: `mock_get_player_ids_cache`
        - `CACHE_MANAGER.is_player_ids_cache_stale`: `mock_is_stale`
        - `CACHE_MANAGER.save_all_caches`: `mock_save_all_caches`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `TEAM_DEFENSE_NAMES`: `mock_team_defense_names`
        - `_update_new_names`: `mock_update_new_names`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.is_player_ids_cache_stale"
            ) as mock_is_stale,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.save_all_caches"
            ) as mock_save_all_caches,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".TEAM_DEFENSE_NAMES",
                {
                    "KC": {
                        "full_name": "Kansas City Chiefs",
                        "first_name": "Kansas City",
                        "last_name": "Chiefs",
                    }
                },
            ),
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                "._update_new_names"
            ) as mock_update_new_names,
        ):
            self.mock_player_ids_cache: dict[str, Any] = {}
            self.mock_get_player_ids_cache = mock_get_player_ids_cache
            self.mock_get_player_ids_cache.return_value = (
                self.mock_player_ids_cache
            )

            self.mock_is_stale = mock_is_stale
            self.mock_is_stale.return_value = True

            self.mock_save_all_caches = mock_save_all_caches

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.return_value = {
                "4046": {
                    "full_name": "Patrick Mahomes",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                    "position": "QB",
                    "team": "KC",
                }
            }

            self.mock_update_new_names = mock_update_new_names

            yield

    def test_does_nothing_when_cache_is_fresh(self):
        """Test does nothing when cache is not stale."""
        self.mock_is_stale.return_value = False

        update_player_ids_cache()

        self.mock_fetch_sleeper_data.assert_not_called()
        self.mock_save_all_caches.assert_not_called()

    def test_fetches_data_when_cache_is_stale(self):
        """Test fetches data from Sleeper API when cache is stale."""
        update_player_ids_cache()

        self.mock_fetch_sleeper_data.assert_called_once_with("players/nfl")

    def test_raises_value_error_when_api_returns_non_dict(self):
        """Test raises ValueError when Sleeper API returns non-dict."""
        self.mock_fetch_sleeper_data.return_value = []

        with pytest.raises(ValueError) as exc_info:
            update_player_ids_cache()

        assert "Expected a dictionary" in str(exc_info.value)

    def test_adds_player_to_cache_with_selected_fields(self):
        """Test adds player to cache with only selected fields."""
        self.mock_fetch_sleeper_data.return_value = {
            "4046": {
                "full_name": "Patrick Mahomes",
                "first_name": "Patrick",
                "last_name": "Mahomes",
                "position": "QB",
                "team": "KC",
                "extra_field": "should_be_ignored",
            }
        }

        update_player_ids_cache()

        assert "4046" in self.mock_player_ids_cache
        assert self.mock_player_ids_cache["4046"]["full_name"] == (
            "Patrick Mahomes"
        )
        assert "extra_field" not in self.mock_player_ids_cache["4046"]

    def test_adds_team_defense_entries(self):
        """Test adds synthetic team defense entries."""
        self.mock_fetch_sleeper_data.return_value = {
            "KC": {"full_name": "Different Name", "position": "DEF"}
        }

        update_player_ids_cache()

        assert "KC" in self.mock_player_ids_cache
        assert self.mock_player_ids_cache["KC"]["full_name"] == (
            "Kansas City Chiefs"
        )
        assert self.mock_player_ids_cache["KC"]["position"] == "DEF"

    def test_fills_missing_defense_entries(self):
        """Test fills in missing defense entries in TEAM_DEFENSE_NAMES."""
        self.mock_fetch_sleeper_data.return_value = {
            "4046": {"full_name": "Player"}
        }

        update_player_ids_cache()

        assert "KC" in self.mock_player_ids_cache
        assert self.mock_player_ids_cache["KC"]["position"] == "DEF"

    def test_calls_update_new_names(self):
        """Test calls _update_new_names with old data."""
        self.mock_player_ids_cache["4046"] = {"full_name": "Pat Mahomes"}
        self.mock_fetch_sleeper_data.return_value = {
            "4046": {"full_name": "Patrick Mahomes"}
        }

        update_player_ids_cache()

        self.mock_update_new_names.assert_called_once()

    def test_saves_all_caches_after_update(self):
        """Test saves all caches after successful update."""
        update_player_ids_cache()

        self.mock_save_all_caches.assert_called_once()


class TestUpdateNewNames:
    """Test _update_new_names function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`: `mock_get_player_ids_cache`
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager_cache`
        - `CACHE_MANAGER.get_player_data_cache`: `mock_get_player_data_cache`
        - `CACHE_MANAGER.get_starters_cache`: `mock_get_starters_cache`
        - `CACHE_MANAGER.get_transaction_ids_cache`: `mock_get_transaction_ids`
        - `CACHE_MANAGER.get_valid_options_cache`: `mock_get_valid_options`
        - `CACHE_MANAGER.get_players_cache`: `mock_get_players_cache`
        - `CACHE_MANAGER.get_image_urls_cache`: `mock_get_image_urls_cache`
        - `_recursive_replace`: `mock_recursive_replace`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.get_player_data_cache"
            ) as mock_get_player_data_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.get_starters_cache"
            ) as mock_get_starters_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.get_transaction_ids_cache"
            ) as mock_get_transaction_ids,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.get_players_cache"
            ) as mock_get_players_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.get_image_urls_cache"
            ) as mock_get_image_urls_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                "._recursive_replace"
            ) as mock_recursive_replace,
        ):
            self.mock_player_ids_cache = {
                "4046": {"full_name": "Patrick Mahomes"}
            }
            self.mock_get_player_ids_cache = mock_get_player_ids_cache
            self.mock_get_player_ids_cache.return_value = (
                self.mock_player_ids_cache
            )

            self.mock_get_manager_cache = mock_get_manager_cache
            self.mock_get_manager_cache.return_value = {}

            self.mock_get_player_data_cache = mock_get_player_data_cache
            self.mock_get_player_data_cache.return_value = {}

            self.mock_get_starters_cache = mock_get_starters_cache
            self.mock_get_starters_cache.return_value = {}

            self.mock_get_transaction_ids = mock_get_transaction_ids
            self.mock_get_transaction_ids.return_value = {}

            self.mock_get_valid_options = mock_get_valid_options
            self.mock_get_valid_options.return_value = {}

            self.mock_get_players_cache = mock_get_players_cache
            self.mock_get_players_cache.return_value = {}

            self.mock_get_image_urls_cache = mock_get_image_urls_cache
            self.mock_get_image_urls_cache.return_value = {}

            self.mock_recursive_replace = mock_recursive_replace
            self.mock_recursive_replace.side_effect = lambda d, o, n: d

            yield

    def test_skips_new_players(self):
        """Test skips players not in old data (new additions)."""
        old_ids: dict[str, Any] = {}

        _update_new_names(old_ids)

        self.mock_recursive_replace.assert_not_called()

    def test_skips_unchanged_names(self):
        """Test skips players whose names haven't changed."""
        old_ids = {"4046": {"full_name": "Patrick Mahomes"}}

        _update_new_names(old_ids)

        self.mock_recursive_replace.assert_not_called()

    def test_updates_all_caches_when_name_changes(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test updates all caches when player name changes.

        Args:
            caplog: pytest caplog fixture
        """
        old_ids = {"4046": {"full_name": "Pat Mahomes"}}

        caplog.set_level(logging.INFO)
        _update_new_names(old_ids)

        assert self.mock_recursive_replace.call_count == 7
        assert "Pat Mahomes" in caplog.text
        assert "Patrick Mahomes" in caplog.text

    def test_logs_name_change(self, caplog: pytest.LogCaptureFixture):
        """Test logs info about name change.

        Args:
            caplog: pytest caplog fixture
        """
        old_ids = {"4046": {"full_name": "Pat Mahomes"}}

        caplog.set_level(logging.INFO)
        _update_new_names(old_ids)

        assert "New Player Name Found" in caplog.text
        assert "changed his name" in caplog.text


class TestRecursiveReplace:
    """Test _recursive_replace function."""

    def test_replaces_string_value(self):
        """Test replaces string value."""
        data = "Hello Pat Mahomes"

        result = _recursive_replace(data, "Pat", "Patrick")

        assert result == "Hello Patrick Mahomes"

    def test_replaces_in_dict_values(self):
        """Test replaces in dictionary values."""
        data = {"name": "Pat Mahomes", "team": "KC"}

        result = _recursive_replace(data, "Pat", "Patrick")

        assert result["name"] == "Patrick Mahomes"
        assert result["team"] == "KC"

    def test_replaces_in_dict_keys(self):
        """Test replaces in dictionary keys."""
        data = {"Pat Mahomes": {"score": 25}}

        result = _recursive_replace(data, "Pat", "Patrick")

        assert "Patrick Mahomes" in result
        assert "Pat Mahomes" not in result

    def test_replaces_in_list_elements(self):
        """Test replaces in list elements."""
        data = ["Pat Mahomes", "Josh Allen"]

        result = _recursive_replace(data, "Pat", "Patrick")

        assert result[0] == "Patrick Mahomes"
        assert result[1] == "Josh Allen"

    def test_replaces_in_nested_structures(self):
        """Test replaces in deeply nested structures."""
        data = {
            "players": [
                {"name": "Pat Mahomes", "stats": {"nickname": "Pat"}}
            ]
        }

        result = _recursive_replace(data, "Pat", "Patrick")

        assert result["players"][0]["name"] == "Patrick Mahomes"
        assert result["players"][0]["stats"]["nickname"] == "Patrick"

    def test_returns_non_string_primitives_unchanged(self):
        """Test returns non-string primitives unchanged."""
        assert _recursive_replace(123, "old", "new") == 123
        assert _recursive_replace(45.67, "old", "new") == 45.67
        assert _recursive_replace(True, "old", "new") is True
        assert _recursive_replace(None, "old", "new") is None

    def test_handles_empty_structures(self):
        """Test handles empty structures."""
        assert _recursive_replace({}, "old", "new") == {}
        assert _recursive_replace([], "old", "new") == []
        assert _recursive_replace("", "old", "new") == ""

    def test_handles_partial_matches(self):
        """Test handles partial string matches."""
        data = "Patrick Mahomes is great"

        result = _recursive_replace(data, "Patrick", "Pat")

        assert result == "Pat Mahomes is great"

    def test_replaces_multiple_occurrences(self):
        """Test replaces multiple occurrences in same string."""
        data = "Pat played well, Pat scored"

        result = _recursive_replace(data, "Pat", "Patrick")

        assert result == "Patrick played well, Patrick scored"
