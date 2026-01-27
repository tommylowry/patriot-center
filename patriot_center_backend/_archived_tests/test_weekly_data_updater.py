"""Unit tests for weekly_data_updater module."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from patriot_center_backend.cache.updaters.manager_data_updater import (
    ManagerMetadataManager,
)
from patriot_center_backend.cache.updaters.weekly_data_updater import (
    _cache_matchup_data,
    _cache_valid_data,
    _cache_week,
    update_weekly_data_caches,
)


@pytest.fixture
def mock_manager_updater() -> ManagerMetadataManager:
    """Create MagicMock for ManagerMetadataManager.

    Returns:
        A MagicMock with ManagerMetadataManager's interface.
    """
    return MagicMock(spec=ManagerMetadataManager)


class TestUpdateWeeklyDataCaches:
    """Test update_weekly_data_caches function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_updater: ManagerMetadataManager):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_starters_cache`: `mock_get_starters_cache`
        - `CACHE_MANAGER.get_valid_options_cache`: `mock_get_valid_options`
        - `CACHE_MANAGER.get_replacement_score_cache`: `mock_get_replacement`
        - `CACHE_MANAGER.save_all_caches`: `mock_save_all_caches`
        - `ManagerMetadataManager`: `mock_manager_updater_class`
        - `get_current_season_and_week`: `mock_get_current`
        - `get_roster_ids`: `mock_get_roster_ids`
        - `LEAGUE_IDS`: `mock_league_ids`
        - `_cache_week`: `mock_cache_week`
        - `retroactively_assign_team_placement_for_player`: `mock_retroactive`
        - `update_replacement_score_cache`: `mock_update_replacement`
        - `get_max_weeks`: `mock_get_max_weeks`

        Args:
            mock_manager_updater: A MagicMock for ManagerMetadataManager

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".CACHE_MANAGER.get_starters_cache"
            ) as mock_get_starters_cache,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".CACHE_MANAGER.save_all_caches"
            ) as mock_save_all_caches,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".ManagerMetadataManager"
            ) as mock_manager_updater_class,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".get_current_season_and_week"
            ) as mock_get_current,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".get_roster_ids"
            ) as mock_get_roster_ids,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".LEAGUE_IDS",
                {2024: "league2024"},
            ),
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                "._cache_week"
            ) as mock_cache_week,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".retroactively_assign_team_placement_for_player"
            ) as mock_retroactive,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".update_replacement_score_cache"
            ) as mock_update_replacement,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".get_max_weeks"
            ) as mock_get_max_weeks,
        ):
            self.mock_starters_cache: dict[str, Any] = {
                "Last_Updated_Season": "0",
                "Last_Updated_Week": 0,
            }
            self.mock_get_starters_cache = mock_get_starters_cache
            self.mock_get_starters_cache.return_value = self.mock_starters_cache

            self.mock_valid_options_cache: dict[str, Any] = {}
            self.mock_get_valid_options = mock_get_valid_options
            self.mock_get_valid_options.return_value = (
                self.mock_valid_options_cache
            )

            self.mock_replacement_cache: dict[str, Any] = {}
            self.mock_get_replacement = mock_get_replacement
            self.mock_get_replacement.return_value = self.mock_replacement_cache

            self.mock_save_all_caches = mock_save_all_caches

            self.mock_manager_updater = mock_manager_updater
            self.mock_manager_updater_class = mock_manager_updater_class
            self.mock_manager_updater_class.return_value = (
                self.mock_manager_updater
            )

            self.mock_get_current = mock_get_current
            self.mock_get_current.return_value = (2024, 5)

            self.mock_get_roster_ids = mock_get_roster_ids
            self.mock_get_roster_ids.return_value = {1: "Tommy", 2: "Mike"}

            self.mock_cache_week = mock_cache_week

            self.mock_retroactive = mock_retroactive

            self.mock_update_replacement = mock_update_replacement

            self.mock_get_max_weeks = mock_get_max_weeks
            self.mock_get_max_weeks.return_value = 5

            yield

    def test_caps_current_week_at_17(self):
        """Test caps current week at 17 for regular season."""
        self.mock_get_current.return_value = (2024, 18)
        self.mock_starters_cache["Last_Updated_Season"] = "2024"
        self.mock_starters_cache["Last_Updated_Week"] = 17

        update_weekly_data_caches()

        self.mock_cache_week.assert_not_called()

    def test_saves_all_caches_at_end(self):
        """Test saves all caches at the end of processing."""
        self.mock_starters_cache["Last_Updated_Season"] = "2024"
        self.mock_starters_cache["Last_Updated_Week"] = 5

        update_weekly_data_caches()

        self.mock_save_all_caches.assert_called_once()

    def test_skips_already_processed_seasons(self):
        """Test skips seasons that are already fully processed."""
        self.mock_starters_cache["Last_Updated_Season"] = "2024"
        self.mock_starters_cache["Last_Updated_Week"] = 5

        update_weekly_data_caches()

        self.mock_cache_week.assert_not_called()

    def test_updates_replacement_score_for_week_18_when_needed(self):
        """Test updates replacement score for week 18 when week > 17."""
        self.mock_get_current.return_value = (2024, 18)
        self.mock_starters_cache["Last_Updated_Season"] = "2024"
        self.mock_starters_cache["Last_Updated_Week"] = 17
        self.mock_replacement_cache["2024"] = {"17": {}}

        update_weekly_data_caches()

        self.mock_update_replacement.assert_called_once_with(2024, 18)

    def test_skips_replacement_update_when_week_18_exists(self):
        """Test skips replacement update when week 18 already cached."""
        self.mock_get_current.return_value = (2024, 18)
        self.mock_starters_cache["Last_Updated_Season"] = "2024"
        self.mock_starters_cache["Last_Updated_Week"] = 17
        self.mock_replacement_cache["2024"] = {"17": {}, "18": {}}

        update_weekly_data_caches()

        self.mock_update_replacement.assert_not_called()

    def test_skips_years_before_last_updated_season(self):
        """Test skips years that are before the last updated season."""
        self.mock_starters_cache["Last_Updated_Season"] = "2024"
        self.mock_starters_cache["Last_Updated_Week"] = 3

        update_weekly_data_caches()

        self.mock_cache_week.assert_called()
        calls = self.mock_cache_week.call_args_list
        years_processed = [call[0][0] for call in calls]
        assert all(year >= 2024 for year in years_processed)

    def test_resets_week_marker_when_advancing_season(self):
        """Test resets Last_Updated_Week when advancing to new season."""
        with patch(
            "patriot_center_backend.cache.updaters.weekly_data_updater"
            ".LEAGUE_IDS",
            {2023: "league2023", 2024: "league2024"},
        ):
            self.mock_starters_cache["Last_Updated_Season"] = "2023"
            self.mock_starters_cache["Last_Updated_Week"] = 17
            self.mock_get_max_weeks.return_value = 17

            update_weekly_data_caches()

            assert self.mock_starters_cache["Last_Updated_Week"] == 0 or (
                self.mock_cache_week.called
            )

    def test_assigns_placements_at_week_17_when_up_to_date(self):
        """Test assigns placements when at week 17 and fully updated."""
        self.mock_get_current.return_value = (2024, 17)
        self.mock_starters_cache["Last_Updated_Season"] = "2024"
        self.mock_starters_cache["Last_Updated_Week"] = 17

        update_weekly_data_caches()

        self.mock_retroactive.assert_called_once()

    def test_assigns_placements_for_previous_year(self):
        """Test retroactively assigns placements for previous completed year."""
        with patch(
            "patriot_center_backend.cache.updaters.weekly_data_updater"
            ".LEAGUE_IDS",
            {2023: "league2023", 2024: "league2024"},
        ):
            self.mock_starters_cache["Last_Updated_Season"] = "0"
            self.mock_starters_cache["Last_Updated_Week"] = 0
            self.mock_get_max_weeks.return_value = 5

            update_weekly_data_caches()

            retroactive_calls = self.mock_retroactive.call_args_list
            years_called = [call[0][0] for call in retroactive_calls]
            assert 2023 in years_called

    def test_processes_weeks_from_scratch_for_new_season(self):
        """Test processes all weeks from 1 when starting fresh season."""
        self.mock_starters_cache["Last_Updated_Season"] = "0"
        self.mock_starters_cache["Last_Updated_Week"] = 0
        self.mock_get_max_weeks.return_value = 3

        update_weekly_data_caches()

        assert self.mock_cache_week.call_count == 3

    def test_processes_weeks_incrementally_for_current_season(self):
        """Test processes only new weeks for current season."""
        self.mock_starters_cache["Last_Updated_Season"] = "2024"
        self.mock_starters_cache["Last_Updated_Week"] = 3
        self.mock_get_max_weeks.return_value = 5

        update_weekly_data_caches()

        assert self.mock_cache_week.call_count == 2
        weeks_processed = [
            call[0][1] for call in self.mock_cache_week.call_args_list
        ]
        assert 4 in weeks_processed
        assert 5 in weeks_processed

    def test_skips_when_no_weeks_to_update(self):
        """Test skips processing when weeks_to_update is empty."""
        self.mock_starters_cache["Last_Updated_Season"] = "2024"
        self.mock_starters_cache["Last_Updated_Week"] = 5
        self.mock_get_max_weeks.return_value = 5

        update_weekly_data_caches()

        self.mock_cache_week.assert_not_called()

    def test_assigns_placements_at_max_weeks(self):
        """Test retroactively assigns placements when reaching max weeks."""
        self.mock_starters_cache["Last_Updated_Season"] = "0"
        self.mock_starters_cache["Last_Updated_Week"] = 0
        self.mock_get_max_weeks.return_value = 2

        update_weekly_data_caches()

        self.mock_retroactive.assert_called()

    def test_updates_replacement_score_at_max_weeks(self):
        """Test updates replacement score for next week at max weeks."""
        self.mock_starters_cache["Last_Updated_Season"] = "0"
        self.mock_starters_cache["Last_Updated_Week"] = 0
        self.mock_get_max_weeks.return_value = 2

        update_weekly_data_caches()

        replacement_calls = self.mock_update_replacement.call_args_list
        weeks_called = [call[0][1] for call in replacement_calls]
        assert 3 in weeks_called

    def test_initializes_starters_cache_for_year(self):
        """Test initializes starters cache structure for new year."""
        self.mock_starters_cache["Last_Updated_Season"] = "0"
        self.mock_starters_cache["Last_Updated_Week"] = 0
        self.mock_get_max_weeks.return_value = 1

        update_weekly_data_caches()

        assert "2024" in self.mock_starters_cache

    def test_initializes_valid_options_cache_for_year(self):
        """Test initializes valid options cache structure for new year."""
        self.mock_starters_cache["Last_Updated_Season"] = "0"
        self.mock_starters_cache["Last_Updated_Week"] = 0
        self.mock_get_max_weeks.return_value = 1

        update_weekly_data_caches()

        assert "2024" in self.mock_valid_options_cache
        assert "managers" in self.mock_valid_options_cache["2024"]
        assert "players" in self.mock_valid_options_cache["2024"]

    def test_updates_progress_markers_after_each_week(self):
        """Test updates Last_Updated_Season and Last_Updated_Week."""
        self.mock_starters_cache["Last_Updated_Season"] = "0"
        self.mock_starters_cache["Last_Updated_Week"] = 0
        self.mock_get_max_weeks.return_value = 2

        update_weekly_data_caches()

        assert self.mock_starters_cache["Last_Updated_Season"] == "2024"
        assert self.mock_starters_cache["Last_Updated_Week"] == 2

    def test_reloads_starters_cache_at_end(self):
        """Test reloads starters cache to remove metadata at end."""
        self.mock_starters_cache["Last_Updated_Season"] = "2024"
        self.mock_starters_cache["Last_Updated_Week"] = 5

        update_weekly_data_caches()

        self.mock_get_starters_cache.assert_any_call(force_reload=True)


class TestCacheWeek:
    """Test _cache_week function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_updater: ManagerMetadataManager):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `LEAGUE_IDS`: `mock_league_ids`
        - `_get_relevant_playoff_roster_ids`: `mock_get_playoff_roster_ids`
        - `_cache_matchup_data`: `mock_cache_matchup_data`
        - `update_replacement_score_cache`: `mock_update_replacement`
        - `update_player_data_cache`: `mock_update_player_data`

        Args:
            mock_manager_updater: Mock ManagerMetadataManager

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".LEAGUE_IDS",
                {2024: "league2024", 2019: "league2019"},
            ),
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                "._get_relevant_playoff_roster_ids"
            ) as mock_get_playoff_roster_ids,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                "._cache_matchup_data"
            ) as mock_cache_matchup_data,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".update_replacement_score_cache"
            ) as mock_update_replacement,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".update_player_data_cache"
            ) as mock_update_player_data,
        ):
            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.return_value = [
                {"roster_id": 1, "starters": ["4046"], "players_points": {}},
                {"roster_id": 2, "starters": ["6744"], "players_points": {}},
            ]

            self.mock_get_playoff_roster_ids = mock_get_playoff_roster_ids
            self.mock_get_playoff_roster_ids.return_value = []

            self.mock_cache_matchup_data = mock_cache_matchup_data

            self.mock_update_replacement = mock_update_replacement
            self.mock_update_player_data = mock_update_player_data

            self.mock_manager_updater = mock_manager_updater

            yield

    def test_fetches_matchups_from_sleeper(self):
        """Test fetches matchups from Sleeper API."""
        roster_ids = {1: "Tommy", 2: "Mike"}

        _cache_week(2024, 5, self.mock_manager_updater, roster_ids)

        self.mock_fetch_sleeper_data.assert_called_with(
            "league/league2024/matchups/5"
        )

    def test_raises_error_when_matchups_not_list(self):
        """Test raises ValueError when matchups response is not a list."""
        self.mock_fetch_sleeper_data.return_value = {}
        roster_ids = {1: "Tommy", 2: "Mike"}

        with pytest.raises(ValueError) as exc_info:
            _cache_week(2024, 5, self.mock_manager_updater, roster_ids)

        assert "not in list form" in str(exc_info.value)

    def test_handles_2019_roster_swap(self):
        """Test handles 2019 weeks 1-3 roster swap from Cody to Tommy."""
        roster_ids = {1: "Cody", 2: "Mike"}

        _cache_week(2019, 2, self.mock_manager_updater, roster_ids)

        calls = self.mock_cache_matchup_data.call_args_list
        manager_names = [call[0][3] for call in calls]
        assert "Tommy" in manager_names

    def test_calls_manager_updater_methods(self):
        """Test calls manager_updater set_roster_id and cache_week_data."""
        roster_ids = {1: "Tommy", 2: "Mike"}

        _cache_week(2024, 5, self.mock_manager_updater, roster_ids)

        assert self.mock_manager_updater.set_roster_id.called
        self.mock_manager_updater.cache_week_data.assert_called_once_with(
            "2024", "5"
        )

    def test_calls_update_replacement_and_player_data(self):
        """Test calls both cache methods."""
        roster_ids = {1: "Tommy", 2: "Mike"}

        _cache_week(2024, 5, self.mock_manager_updater, roster_ids)

        self.mock_update_replacement.assert_called_once_with(2024, 5)
        self.mock_update_player_data.assert_called_once_with(
            2024, 5, roster_ids
        )

    def test_skips_if_roster_id_of_matchup_not_in_roster_ids(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test logs warning when roster_id of matchup not in roster_ids.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_fetch_sleeper_data.return_value = [
            {"roster_id": 1, "starters": ["4046"], "players_points": {}},
            {"roster_id": 3, "starters": ["6744"], "players_points": {}},
        ]

        roster_ids = {1: "Tommy", 2: "Mike"}

        _cache_week(2024, 5, self.mock_manager_updater, roster_ids)

        assert "Roster ID 3 in matchup not found" in caplog.text

        self.mock_cache_matchup_data.assert_called_once_with(
            "2024",
            "5",
            {"roster_id": 1, "starters": ["4046"], "players_points": {}},
            "Tommy",
        )

    def test_skips_if_roster_id_not_in_playoffs(self):
        """Test skips if roster_id not in playoffs."""
        roster_ids = {1: "Tommy", 2: "Mike"}

        self.mock_get_playoff_roster_ids.return_value = [3]

        _cache_week(2024, 15, self.mock_manager_updater, roster_ids)

        self.mock_cache_matchup_data.assert_not_called()


class TestCacheMatchupData:
    """Test _cache_matchup_data function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_starters_cache`: `mock_get_starters_cache`
        - `CACHE_MANAGER.get_player_ids_cache`: `mock_get_player_ids_cache`
        - `_cache_valid_data`: `mock_cache_valid_data`
        - `update_players_cache`: `mock_update_players_cache`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".CACHE_MANAGER.get_starters_cache"
            ) as mock_get_starters_cache,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids_cache,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                "._cache_valid_data"
            ) as mock_cache_valid_data,
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".update_players_cache"
            ) as mock_update_players_cache,
        ):
            self.mock_starters_cache: dict[str, Any] = {"2024": {"5": {}}}
            self.mock_get_starters_cache = mock_get_starters_cache
            self.mock_get_starters_cache.return_value = self.mock_starters_cache

            self.mock_player_ids_cache = {
                "4046": {
                    "full_name": "Patrick Mahomes",
                    "position": "QB",
                },
            }
            self.mock_get_player_ids_cache = mock_get_player_ids_cache
            self.mock_get_player_ids_cache.return_value = (
                self.mock_player_ids_cache
            )

            self.mock_cache_valid_data = mock_cache_valid_data
            self.mock_update_players_cache = mock_update_players_cache

            yield

    def test_adds_manager_data_to_starters_cache(self):
        """Test adds manager data to starters cache."""
        matchup = {
            "starters": ["4046"],
            "players_points": {"4046": 25.0},
        }

        _cache_matchup_data("2024", "5", matchup, "Tommy")

        assert "Tommy" in self.mock_starters_cache["2024"]["5"]
        manager_data = self.mock_starters_cache["2024"]["5"]["Tommy"]
        assert "Patrick Mahomes" in manager_data
        assert manager_data["Patrick Mahomes"]["points"] == 25.0

    def test_calculates_total_points(self):
        """Test calculates and rounds total points correctly."""
        matchup = {
            "starters": ["4046"],
            "players_points": {"4046": 25.123456},
        }

        _cache_matchup_data("2024", "5", matchup, "Tommy")

        manager_data = self.mock_starters_cache["2024"]["5"]["Tommy"]
        assert manager_data["Total_Points"] == 25.12

    def test_skips_unknown_players(self):
        """Test skips players not in player_ids_cache."""
        matchup = {
            "starters": ["9999"],
            "players_points": {"9999": 10.0},
        }

        _cache_matchup_data("2024", "5", matchup, "Tommy")

        manager_data = self.mock_starters_cache["2024"]["5"]["Tommy"]
        assert manager_data["Total_Points"] == 0.0

    def test_calls_update_players_cache(self):
        """Test calls update_players_cache for each player."""
        matchup = {
            "starters": ["4046"],
            "players_points": {"4046": 25.0},
        }

        _cache_matchup_data("2024", "5", matchup, "Tommy")

        self.mock_update_players_cache.assert_called_once_with("4046")

    def test_skips_player_if_no_position(self):
        """Test skips player if no position."""
        self.mock_player_ids_cache["9999"] = {"full_name": "Unknown Player"}

        matchup = {  # Player 9999 has no position
            "starters": ["4046", "9999"],
            "players_points": {"9999": 10.0, "4046": 25.0},
        }

        _cache_matchup_data("2024", "5", matchup, "Tommy")

        manager_data = self.mock_starters_cache["2024"]["5"]["Tommy"]
        assert manager_data["Total_Points"] == 25.0
        assert "9999" not in manager_data
        assert "Patrick Mahomes" in manager_data


class TestCacheValidData:
    """Test _cache_valid_data function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_valid_options_cache`: `mock_get_valid_options`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options,
        ):
            self.mock_valid_options_cache: dict[str, Any] = {
                "2024": {
                    "managers": [],
                    "players": [],
                    "positions": [],
                    "weeks": [],
                    "5": {
                        "managers": [],
                        "players": [],
                        "positions": [],
                    },
                }
            }
            self.mock_get_valid_options = mock_get_valid_options
            self.mock_get_valid_options.return_value = (
                self.mock_valid_options_cache
            )

            yield

    def test_adds_manager_to_year_level(self):
        """Test adds manager to year level managers list."""
        _cache_valid_data("2024", "5", "Tommy", "Patrick Mahomes", "QB")

        assert "Tommy" in self.mock_valid_options_cache["2024"]["managers"]

    def test_adds_manager_to_week_level(self):
        """Test adds manager to week level managers list."""
        _cache_valid_data("2024", "5", "Tommy", "Patrick Mahomes", "QB")

        assert "Tommy" in self.mock_valid_options_cache["2024"]["5"]["managers"]

    def test_adds_player_to_all_levels(self):
        """Test adds player to year, week, and manager levels."""
        _cache_valid_data("2024", "5", "Tommy", "Patrick Mahomes", "QB")

        year_lvl = self.mock_valid_options_cache["2024"]
        week_lvl = year_lvl["5"]
        mgr_lvl = week_lvl["Tommy"]

        assert "Patrick Mahomes" in year_lvl["players"]
        assert "Patrick Mahomes" in week_lvl["players"]
        assert "Patrick Mahomes" in mgr_lvl["players"]

    def test_adds_position_to_all_levels(self):
        """Test adds position to year, week, and manager levels."""
        _cache_valid_data("2024", "5", "Tommy", "Patrick Mahomes", "QB")

        year_lvl = self.mock_valid_options_cache["2024"]
        week_lvl = year_lvl["5"]
        mgr_lvl = week_lvl["Tommy"]

        assert "QB" in year_lvl["positions"]
        assert "QB" in week_lvl["positions"]
        assert "QB" in mgr_lvl["positions"]

    def test_creates_manager_entry_if_not_exists(self):
        """Test creates manager entry in week if it doesn't exist."""
        _cache_valid_data("2024", "5", "Tommy", "Patrick Mahomes", "QB")

        assert "Tommy" in self.mock_valid_options_cache["2024"]["5"]

    def test_does_not_duplicate_entries(self):
        """Test does not add duplicate entries."""
        _cache_valid_data("2024", "5", "Tommy", "Patrick Mahomes", "QB")
        _cache_valid_data("2024", "5", "Tommy", "Patrick Mahomes", "QB")

        year_lvl = self.mock_valid_options_cache["2024"]
        assert year_lvl["managers"].count("Tommy") == 1
        assert year_lvl["players"].count("Patrick Mahomes") == 1
