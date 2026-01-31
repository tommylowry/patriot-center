"""Unit tests for player_ids_updater module."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from patriot_center_backend.cache.updaters.player_ids_updater import (
    _add_player_id_entry,
    _apply_full_name,
    _fill_missing_defenses,
    update_player_ids_cache,
)


class TestUpdatePlayerIdsCache:
    """Test update_player_ids_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.is_cache_stale`: `mock_is_cache_stale`
        - `fetch_all_player_ids`: `mock_fetch_all_player_ids`
        - `_add_player_id_entry`: `mock_add_player_id_entry`
        - `_fill_missing_defenses`: `mock_fill_missing_defenses`
        - `CacheSynchronizer`: `mock_cache_synchronizer_class`
        - `CACHE_MANAGER.save_player_ids_cache`: `mock_save_player_ids`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.is_cache_stale"
            ) as mock_is_cache_stale,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".fetch_all_player_ids"
            ) as mock_fetch_all_player_ids,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                "._add_player_id_entry"
            ) as mock_add_player_id_entry,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                "._fill_missing_defenses"
            ) as mock_fill_missing_defenses,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CacheSynchronizer"
            ) as mock_cache_synchronizer_class,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".CACHE_MANAGER.save_player_ids_cache"
            ) as mock_save_player_ids,
        ):
            self.mock_is_cache_stale = mock_is_cache_stale
            self.mock_is_cache_stale.return_value = True

            self.mock_fetch_all_player_ids = mock_fetch_all_player_ids
            self.mock_fetch_all_player_ids.return_value = {
                "4046": {
                    "full_name": "Patrick Mahomes",
                    "first_name": "Patrick",
                    "last_name": "Mahomes",
                    "position": "QB",
                },
            }

            self.mock_add_player_id_entry = mock_add_player_id_entry
            self.mock_fill_missing_defenses = mock_fill_missing_defenses

            self.mock_synchronizer_instance = MagicMock()
            mock_cache_synchronizer_class.return_value = (
                self.mock_synchronizer_instance
            )
            self.mock_cache_synchronizer_class = mock_cache_synchronizer_class

            self.mock_save_player_ids = mock_save_player_ids

            yield

    def test_returns_early_when_cache_not_stale(self):
        """Test returns early when cache is not stale."""
        self.mock_is_cache_stale.return_value = False

        update_player_ids_cache()

        self.mock_fetch_all_player_ids.assert_not_called()

    def test_fetches_player_ids_when_stale(self):
        """Test fetches player IDs from Sleeper when cache is stale."""
        update_player_ids_cache()

        self.mock_fetch_all_player_ids.assert_called_once()

    def test_calls_add_player_id_entry_for_each_player(self):
        """Test calls _add_player_id_entry for each fetched player."""
        update_player_ids_cache()

        self.mock_add_player_id_entry.assert_called_once()

    def test_calls_fill_missing_defenses(self):
        """Test calls _fill_missing_defenses."""
        update_player_ids_cache()

        self.mock_fill_missing_defenses.assert_called_once()

    def test_calls_cache_synchronizer(self):
        """Test calls CacheSynchronizer.synchronize."""
        update_player_ids_cache()

        self.mock_synchronizer_instance.synchronize.assert_called_once()

    def test_saves_player_ids_cache(self):
        """Test saves the new player IDs cache."""
        update_player_ids_cache()

        self.mock_save_player_ids.assert_called_once()

    def test_checks_staleness_for_player_ids(self):
        """Test checks staleness for 'player_ids' cache."""
        update_player_ids_cache()

        self.mock_is_cache_stale.assert_called_once_with("player_ids")


class TestAddPlayerIdEntry:
    """Test _add_player_id_entry function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `_apply_full_name`: `mock_apply_full_name`

        Yields:
            None
        """
        with patch(
            "patriot_center_backend.cache.updaters.player_ids_updater"
            "._apply_full_name"
        ) as mock_apply_full_name:
            self.mock_apply_full_name = mock_apply_full_name

            yield

    def test_adds_entry_with_kept_fields(self):
        """Test adds entry with only FIELDS_TO_KEEP."""
        cache: dict[str, dict[str, Any]] = {}
        player_info = {
            "full_name": "Patrick Mahomes",
            "first_name": "Patrick",
            "last_name": "Mahomes",
            "position": "QB",
            "team": "KC",
            "age": 28,
            "years_exp": 7,
            "college": "Texas Tech",
            "depth_chart_position": "QB",
            "fantasy_positions": ["QB"],
            "number": 15,
            "some_extra_field": "should_not_be_kept",
        }

        _add_player_id_entry("4046", player_info, cache)

        assert "4046" in cache
        assert cache["4046"]["full_name"] == "Patrick Mahomes"
        assert cache["4046"]["position"] == "QB"
        assert "some_extra_field" not in cache["4046"]

    def test_calls_apply_full_name(self):
        """Test calls _apply_full_name on player_info."""
        cache: dict[str, dict[str, Any]] = {}
        player_info = {"full_name": "Patrick Mahomes"}

        _add_player_id_entry("4046", player_info, cache)

        self.mock_apply_full_name.assert_called_once_with(player_info)

    def test_missing_fields_stored_as_none(self):
        """Test missing fields from FIELDS_TO_KEEP are stored as None."""
        cache: dict[str, dict[str, Any]] = {}
        player_info = {"full_name": "Patrick Mahomes"}

        _add_player_id_entry("4046", player_info, cache)

        assert cache["4046"]["position"] is None
        assert cache["4046"]["team"] is None


class TestApplyFullName:
    """Test _apply_full_name function."""

    def test_does_nothing_when_full_name_exists(self):
        """Test does not modify player_info when full_name already exists."""
        player_info = {
            "full_name": "Patrick Mahomes",
            "first_name": "Patrick",
            "last_name": "Mahomes",
        }

        _apply_full_name(player_info)

        assert player_info["full_name"] == "Patrick Mahomes"

    def test_constructs_full_name_from_first_and_last(self):
        """Test constructs full_name from first_name and last_name."""
        player_info = {
            "first_name": "Patrick",
            "last_name": "Mahomes",
        }

        _apply_full_name(player_info)

        assert player_info["full_name"] == "Patrick Mahomes"

    def test_sets_none_when_both_names_missing(self):
        """Test sets full_name to None when both names are missing."""
        player_info: dict[str, Any] = {}

        _apply_full_name(player_info)

        assert player_info["full_name"] is None

    def test_handles_only_first_name(self):
        """Test handles case with only first_name."""
        player_info = {"first_name": "Patrick"}

        _apply_full_name(player_info)

        assert player_info["full_name"] == "Patrick "

    def test_handles_only_last_name(self):
        """Test handles case with only last_name."""
        player_info = {"last_name": "Mahomes"}

        _apply_full_name(player_info)

        assert player_info["full_name"] == " Mahomes"


class TestFillMissingDefenses:
    """Test _fill_missing_defenses function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_defense_entries`: `mock_get_defense_entries`
        - `_add_player_id_entry`: `mock_add_player_id_entry`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                ".get_defense_entries"
            ) as mock_get_defense_entries,
            patch(
                "patriot_center_backend.cache.updaters.player_ids_updater"
                "._add_player_id_entry"
            ) as mock_add_player_id_entry,
        ):
            self.mock_get_defense_entries = mock_get_defense_entries
            self.mock_get_defense_entries.return_value = {
                "OAK": {
                    "full_name": "Las Vegas Raiders",
                    "position": "DEF",
                },
                "SEA": {
                    "full_name": "Seattle Seahawks",
                    "position": "DEF",
                },
            }
            self.mock_add_player_id_entry = mock_add_player_id_entry

            yield

    def test_adds_missing_defense_entries(self):
        """Test adds defense entries that are not in cache."""
        cache: dict[str, dict[str, Any]] = {}

        _fill_missing_defenses(cache)

        assert self.mock_add_player_id_entry.call_count == 2

    def test_skips_existing_defense_entries(self):
        """Test skips defense entries already in cache."""
        cache: dict[str, dict[str, Any]] = {
            "SEA": {"full_name": "Seattle Seahawks"},
        }

        _fill_missing_defenses(cache)

        assert self.mock_add_player_id_entry.call_count == 1
