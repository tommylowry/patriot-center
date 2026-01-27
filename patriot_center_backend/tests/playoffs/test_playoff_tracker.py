"""Unit tests for playoff_tracker module."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from patriot_center_backend.cache.updaters.manager_data_updater import (
    ManagerMetadataManager,
)
from patriot_center_backend.playoffs.playoff_tracker import (
    assign_placements_retroactively,
    get_playoff_placements,
    get_playoff_roster_ids,
)


class TestGetPlayoffRosterIds:
    """Test get_playoff_roster_ids function."""

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
                "patriot_center_backend.playoffs.playoff_tracker"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
        ):
            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data

            yield

    def test_returns_empty_list_for_regular_season_pre_2021(self):
        """Test returns empty list for regular season weeks pre-2021."""
        result = get_playoff_roster_ids(2020, 13, "league123")

        assert result == []
        self.mock_fetch_sleeper_data.assert_not_called()

    def test_returns_empty_list_for_regular_season_2021_plus(self):
        """Test returns empty list for regular season weeks 2021+."""
        result = get_playoff_roster_ids(2024, 14, "league123")

        assert result == []
        self.mock_fetch_sleeper_data.assert_not_called()

    def test_fetches_winners_bracket_for_playoff_week_pre_2021(self):
        """Test fetches winners bracket for playoff weeks."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 1, "t1": 1, "t2": 2},
            {"r": 1, "t1": 3, "t2": 4},
        ]

        result = get_playoff_roster_ids(2019, 14, "league123")

        self.mock_fetch_sleeper_data.assert_called_once_with(
            "league/league123/winners_bracket"
        )
        assert 1 in result
        assert 2 in result

    def test_fetches_winners_bracket_for_championship_pre_2021(self):
        """Test fetches winners bracket for playoff weeks."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 3, "t1": 1, "t2": 2},
            {"r": 3, "t1": 3, "t2": 4},
        ]

        result = get_playoff_roster_ids(2019, 16, "league123")

        self.mock_fetch_sleeper_data.assert_called_once_with(
            "league/league123/winners_bracket"
        )
        assert 1 in result
        assert 2 in result

    def test_fetches_winners_bracket_for_playoff_week(self):
        """Test fetches winners bracket for playoff weeks."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 1, "t1": 1, "t2": 2},
            {"r": 1, "t1": 3, "t2": 4},
        ]

        result = get_playoff_roster_ids(2024, 15, "league123")

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

        result = get_playoff_roster_ids(2024, 15, "league123")

        assert 3 not in result
        assert 4 not in result

    def test_raises_error_for_week_17_pre_2021(self):
        """Test raises ValueError for week 17 in pre-2021 seasons."""
        self.mock_fetch_sleeper_data.return_value = []

        with pytest.raises(ValueError) as exc_info:
            get_playoff_roster_ids(2020, 17, "league123")

        assert "Cannot get playoff roster IDs for week 17" in str(
            exc_info.value
        )

    def test_raises_error_when_api_returns_non_list(self):
        """Test raises ValueError when API returns non-list."""
        self.mock_fetch_sleeper_data.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            get_playoff_roster_ids(2024, 15, "league123")

        assert "Cannot get playoff roster IDs" in str(exc_info.value)

    def test_raises_error_when_no_rosters_found(self):
        """Test raises ValueError when no rosters found for round."""
        self.mock_fetch_sleeper_data.return_value = [
            {"r": 2, "t1": 1, "t2": 2},
        ]

        with pytest.raises(ValueError) as exc_info:
            get_playoff_roster_ids(2024, 15, "league123")

        assert "Cannot get playoff roster IDs" in str(exc_info.value)


class TestGetPlayoffPlacements:
    """Test get_playoff_placements function."""

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
                "patriot_center_backend.playoffs.playoff_tracker"
                ".fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                "patriot_center_backend.playoffs.playoff_tracker"
                ".LEAGUE_IDS",
                {2024: "league2024"},
            ),
            patch(
                "patriot_center_backend.playoffs.playoff_tracker"
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

        result = get_playoff_placements(2024)

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

        result = get_playoff_placements(2024)

        assert result == {}
        assert "Playoff Bracket return not in list form" in caplog.text

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

        result = get_playoff_placements(2024)

        assert result == {}
        assert "Rosters return not in list form" in caplog.text

    def test_returns_empty_dict_when_users_not_list(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns empty dict when rosters response is not a list.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_fetch_sleeper_data.side_effect = [
            [{"w": 1, "l": 2}, {"w": 3}],
            [],
            {},
        ]

        result = get_playoff_placements(2024)

        assert result == {}
        assert "Users return not in list form" in caplog.text

class TestRetroactivelyAssignTeamPlacementForPlayer:
    """Test retroactively_assign_team_placement_for_player function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_starters_cache`: `mock_get_starters_cache`
        - `get_playoff_placements`: `mock_get_placement`
        - `ManagerMetadataManager`: `mock_manager_metadata_manager`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.playoffs.playoff_tracker"
                ".CACHE_MANAGER.get_starters_cache"
            ) as mock_get_starters_cache,
            patch(
                "patriot_center_backend.playoffs.playoff_tracker"
                ".get_playoff_placements"
            ) as mock_get_placements,
            patch(
                "patriot_center_backend.playoffs.playoff_tracker"
                ".ManagerMetadataManager"
            ) as mock_manager_metadata_manager,
        ):
            self.mock_starters_cache: dict[str, Any] = {
                "2024": {
                    "15": {
                        "Tommy": {
                            "Total_Points": 120.0,
                            "Patrick Mahomes": {
                                "points": 25.0,
                                "position": "QB",
                            },
                        },
                    },
                    "16": {
                        "Tommy": {
                            "Total_Points": 115.0,
                            "Patrick Mahomes": {
                                "points": 22.0,
                                "position": "QB",
                            },
                        },
                    },
                    "17": {
                        "Tommy": {
                            "Total_Points": 130.0,
                            "Patrick Mahomes": {
                                "points": 28.0,
                                "position": "QB",
                            },
                        },
                    },
                }
            }
            self.mock_get_starters_cache = mock_get_starters_cache
            self.mock_get_starters_cache.return_value = self.mock_starters_cache

            self.mock_get_placements = mock_get_placements
            self.mock_get_placements.return_value = {"Tommy": 1}

            self.mock_manager_updater_instance: ManagerMetadataManager = (
                MagicMock(spec=ManagerMetadataManager)
            )
            self.mock_manager_metadata_manager = mock_manager_metadata_manager
            self.mock_manager_metadata_manager.return_value = (
                self.mock_manager_updater_instance
            )

            yield

    def test_assigns_placement_to_players(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test assigns placement to players in playoff weeks.

        Args:
            caplog: pytest caplog fixture
        """
        assign_placements_retroactively(2024)

        player_data = (
            self.mock_starters_cache["2024"]["15"]["Tommy"]["Patrick Mahomes"]
        )
        assert player_data["placement"] == 1

    def test_calls_manager_updater_set_playoff_placements(self):
        """Test calls manager_updater.set_playoff_placements."""
        assign_placements_retroactively(2024)

        (
            self.mock_manager_updater_instance
            .set_playoff_placements
            .assert_called_once_with({"Tommy": 1}, "2024")
        )

    def test_returns_early_when_no_placements(self):
        """Test returns early when no placements found."""
        self.mock_get_placements.return_value = {}

        assign_placements_retroactively(2024)

        (
            self.mock_manager_updater_instance
            .set_playoff_placements
            .assert_not_called()
        )

    def test_returns_early_when_placement_already_assigned(self):
        """Test returns early when placement already assigned."""
        player = (
            self.mock_starters_cache["2024"]["15"]["Tommy"]["Patrick Mahomes"]
        )
        player["placement"] = 1

        assign_placements_retroactively(2024)

        (
            self.mock_manager_updater_instance
            .set_playoff_placements
            .assert_called_once()
        )

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
        self.mock_get_placements.return_value = {"Tommy": 1}

        assign_placements_retroactively(2020)

        player_data = (
            self.mock_starters_cache["2020"]["14"]["Tommy"]["Patrick Mahomes"]
        )
        assert player_data["placement"] == 1
