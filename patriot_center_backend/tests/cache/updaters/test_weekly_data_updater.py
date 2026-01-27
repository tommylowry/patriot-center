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
    _get_playoff_placement,
    _get_relevant_playoff_roster_ids,
    retroactively_assign_team_placement_for_player,
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


class TestGetRelevantPlayoffRosterIds:
    """Test _get_relevant_playoff_roster_ids function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
        ):
            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data

            yield

    def test_returns_empty_list_for_regular_season_pre_2021(self):
        """Test returns empty list for regular season weeks pre-2021."""
        result = _get_relevant_playoff_roster_ids(2020, 13, "league123")

        assert result == []
        self.mock_fetch_sleeper_data.assert_not_called()

    def test_returns_empty_list_for_regular_season_2021_plus(self):
        """Test returns empty list for regular season weeks 2021+."""
        result = _get_relevant_playoff_roster_ids(2024, 14, "league123")

        assert result == []
        self.mock_fetch_sleeper_data.assert_not_called()

    def test_fetches_winners_bracket_for_playoff_week(self):
        """Test fetches winners bracket for playoff weeks."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 1, "t1": 1, "t2": 2},
            {"r": 1, "t1": 3, "t2": 4},
        ]

        result = _get_relevant_playoff_roster_ids(2024, 15, "league123")

        self.mock_fetch_sleeper_data.assert_called_once_with(
            "league/league123/winners_bracket"
        )
        assert 1 in result
        assert 2 in result

    def test_excludes_consolation_matchups(self):
        """Test excludes consolation bracket matchups (p=5)."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 1, "t1": 1, "t2": 2},
            {"r": 1, "t1": 3, "t2": 4, "p": 5},
        ]

        result = _get_relevant_playoff_roster_ids(2024, 15, "league123")

        assert 3 not in result
        assert 4 not in result

    def test_raises_error_for_week_17_pre_2021(self):
        """Test raises ValueError for week 17 in pre-2021 seasons."""
        self.mock_fetch_sleeper_data.return_value = []

        with pytest.raises(ValueError) as exc_info:
            _get_relevant_playoff_roster_ids(2020, 17, "league123")

        assert "Cannot get playoff roster IDs for week 17" in str(
            exc_info.value
        )

    def test_raises_error_when_api_returns_non_list(self):
        """Test raises ValueError when API returns non-list."""
        self.mock_fetch_sleeper_data.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            _get_relevant_playoff_roster_ids(2024, 15, "league123")

        assert "Cannot get playoff roster IDs" in str(exc_info.value)

    def test_raises_error_when_no_rosters_found(self):
        """Test raises ValueError when no rosters found for round."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 2, "t1": 1, "t2": 2},
        ]

        with pytest.raises(ValueError) as exc_info:
            _get_relevant_playoff_roster_ids(2024, 15, "league123")

        assert "Cannot get playoff roster IDs" in str(exc_info.value)


class TestGetPlayoffPlacement:
    """Test _get_playoff_placement function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `LEAGUE_IDS`: `mock_league_ids`
        - `USERNAME_TO_REAL_NAME`: `mock_username_to_real_name`

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
                {2024: "league2024"},
            ),
            patch(
                "patriot_center_backend.cache.updaters.weekly_data_updater"
                ".USERNAME_TO_REAL_NAME",
                {"tommy_user": "Tommy", "mike_user": "Mike", "joe_user": "Joe"},
            ),
        ):
            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data

            yield

    def test_returns_placements_for_top_three(self):
        """Test returns correct placements for 1st, 2nd, and 3rd place."""
        self.mock_fetch_sleeper_data.side_effect = [
            [
                {"r": 2, "t1": 1, "t2": 2, "w": 1, "l": 2},
                {"r": 2, "t1": 3, "t2": 4, "w": 3, "l": 4},
            ],
            [
                {"roster_id": 1, "owner_id": "user1"},
                {"roster_id": 2, "owner_id": "user2"},
                {"roster_id": 3, "owner_id": "user3"},
            ],
            [
                {"user_id": "user1", "display_name": "tommy_user"},
                {"user_id": "user2", "display_name": "mike_user"},
                {"user_id": "user3", "display_name": "joe_user"},
            ],
        ]

        result = _get_playoff_placement(2024)

        assert result["Tommy"] == 1
        assert result["Mike"] == 2
        assert result["Joe"] == 3

    def test_returns_empty_dict_when_bracket_not_list(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns empty dict when bracket response is not a list.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_fetch_sleeper_data.side_effect = [
            {},
            [],
            [],
        ]

        result = _get_playoff_placement(2024)

        assert result == {}
        assert "not in list form" in caplog.text

    def test_returns_empty_dict_when_rosters_not_list(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns empty dict when rosters response is not a list.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_fetch_sleeper_data.side_effect = [
            [{"w": 1, "l": 2}, {"w": 3}],
            {},
            [],
        ]

        result = _get_playoff_placement(2024)

        assert result == {}


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


class TestRetroactivelyAssignTeamPlacementForPlayer:
    """Test retroactively_assign_team_placement_for_player function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_manager_updater: ManagerMetadataManager):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_starters_cache`: `mock_get_starters_cache`
        - `_get_playoff_placement`: `mock_get_placement`

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
                "._get_playoff_placement"
            ) as mock_get_placement,
        ):
            self.mock_starters_cache: dict[str, Any] = {
                "2024": {
                    "15": {
                        "Tommy": {
                            "Total_Points": 120.0,
                            "Patrick Mahomes": {
                                "points": 25.0, "position": "QB"
                            },
                        },
                    },
                    "16": {
                        "Tommy": {
                            "Total_Points": 115.0,
                            "Patrick Mahomes": {
                                "points": 22.0, "position": "QB"
                            },
                        },
                    },
                    "17": {
                        "Tommy": {
                            "Total_Points": 130.0,
                            "Patrick Mahomes": {
                                "points": 28.0, "position": "QB"
                            },
                        },
                    },
                }
            }
            self.mock_get_starters_cache = mock_get_starters_cache
            self.mock_get_starters_cache.return_value = self.mock_starters_cache

            self.mock_get_placement = mock_get_placement
            self.mock_get_placement.return_value = {"Tommy": 1}

            self.mock_manager_updater = mock_manager_updater

            yield

    def test_assigns_placement_to_players(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test assigns placement to players in playoff weeks.

        Args:
            caplog: pytest caplog fixture
        """
        retroactively_assign_team_placement_for_player(
            2024, self.mock_manager_updater
        )

        player_data = (
            self.mock_starters_cache["2024"]["15"]["Tommy"]["Patrick Mahomes"]
        )
        assert player_data["placement"] == 1

    def test_calls_manager_updater_set_playoff_placements(self):
        """Test calls manager_updater.set_playoff_placements."""
        retroactively_assign_team_placement_for_player(
            2024, self.mock_manager_updater
        )

        (
            self.mock_manager_updater
            .set_playoff_placements
            .assert_called_once_with({"Tommy": 1}, "2024")
        )

    def test_returns_early_when_no_placements(self):
        """Test returns early when no placements found."""
        self.mock_get_placement.return_value = {}

        retroactively_assign_team_placement_for_player(
            2024, self.mock_manager_updater
        )

        self.mock_manager_updater.set_playoff_placements.assert_not_called()

    def test_returns_early_when_placement_already_assigned(self):
        """Test returns early when placement already assigned."""
        player = (
            self.mock_starters_cache["2024"]["15"]["Tommy"]["Patrick Mahomes"]
        )
        player["placement"] = 1

        retroactively_assign_team_placement_for_player(
            2024, self.mock_manager_updater
        )

        self.mock_manager_updater.set_playoff_placements.assert_called_once()

    def test_uses_correct_weeks_for_pre_2021(self):
        """Test uses weeks 14-16 for pre-2021 seasons."""
        self.mock_starters_cache["2020"] = {
            "14": {
                "Tommy": {
                    "Total_Points": 120.0,
                    "Patrick Mahomes": {"points": 25.0},
                },
            },
        }
        self.mock_get_placement.return_value = {"Tommy": 1}

        retroactively_assign_team_placement_for_player(
            2020, self.mock_manager_updater
        )

        player_data = (
            self.mock_starters_cache["2020"]["14"]["Tommy"]["Patrick Mahomes"]
        )
        assert player_data["placement"] == 1
