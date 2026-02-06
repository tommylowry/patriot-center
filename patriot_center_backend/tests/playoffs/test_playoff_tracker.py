"""Unit tests for playoff_tracker module."""

from typing import Any
from unittest.mock import patch

import pytest
from patriot_center_backend.playoffs.playoff_tracker import (
    _manager_cache_set_playoff_placements,
    assign_placements_retroactively,
    get_playoff_placements,
)


class TestGetPlayoffPlacements:
    """Test get_playoff_placements function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
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


class TestAssignPlacementsRetroactively:
    """Test assign_placements_retroactively function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_starters_cache`: `mock_get_starters_cache`
        - `get_playoff_placements`: `mock_get_placement`
        - `_manager_cache_set_playoff_placements`: `mock_manager_set`

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
                "._manager_cache_set_playoff_placements"
            ) as mock_manager_set,
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

            self.mock_manager_set = mock_manager_set

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

    def test_calls_manager_cache_set_playoff_placements(self):
        """Test calls manager_cache_set_playoff_placements."""
        assign_placements_retroactively(2024)

        self.mock_manager_set.assert_called_once_with({"Tommy": 1}, 2024)

    def test_returns_early_when_no_placements(self):
        """Test returns early when no placements found."""
        self.mock_get_placements.return_value = {}

        assign_placements_retroactively(2024)

        self.mock_manager_set.assert_not_called()

    def test_returns_early_when_placement_already_assigned(self):
        """Test returns early when placement already assigned."""
        player = (
            self.mock_starters_cache["2024"]["15"]["Tommy"]["Patrick Mahomes"]
        )
        player["placement"] = 1

        assign_placements_retroactively(2024)

        self.mock_manager_set.assert_called_once()

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


class TestManagerCacheSetPlayoffPlacements:
    """Test manager_cache_set_playoff_placements function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_manager_cache`: `mock_get_manager`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.playoffs.playoff_tracker"
                ".CACHE_MANAGER.get_manager_cache"
            ) as mock_get_manager,
        ):
            self.mock_manager_cache = {}
            self.mock_get_manager = mock_get_manager
            self.mock_get_manager.return_value = self.mock_manager_cache

            yield

    def test_set_playoff_placements_updates_cache(self):
        """Test that playoff placements are added to cache."""
        placements = {"Manager 1": 1, "Manager 2": 2}
        self.mock_manager_cache.update(
            {"Manager 1": {"summary": {"overall_data": {"placement": {}}}}}
        )

        _manager_cache_set_playoff_placements(placements, 2023)

        manager_summary = self.mock_manager_cache["Manager 1"]["summary"]
        assert manager_summary["overall_data"]["placement"]["2023"] == 1

    def test_set_playoff_placements_skips_unknown_managers(self):
        """Test that unknown managers are skipped."""
        placements = {"Unknown Manager": 1}

        # Should not raise error
        _manager_cache_set_playoff_placements(placements, 2023)
