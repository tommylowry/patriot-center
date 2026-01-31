"""Unit tests for starters_updater module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters.starters_updater import (
    update_starters_cache,
)


class TestUpdateStartersCache:
    """Test update_starters_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined set of values when
        accessed.
        - `CACHE_MANAGER.get_starters_cache`: `mock_get_starters_cache`
        - `get_player_name`: `mock_get_player_name`
        - `get_player_position`: `mock_get_player_position`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.starters_updater"
                ".CACHE_MANAGER.get_starters_cache"
            ) as mock_get_starters_cache,
            patch(
                "patriot_center_backend.cache.updaters.starters_updater"
                ".get_player_name"
            ) as mock_get_player_name,
            patch(
                "patriot_center_backend.cache.updaters.starters_updater"
                ".get_player_position"
            ) as mock_get_player_position,
        ):
            self.mock_starters_cache: dict = {}
            mock_get_starters_cache.return_value = self.mock_starters_cache

            self.mock_get_player_name = mock_get_player_name
            self.mock_get_player_position = mock_get_player_position

            # Default return values for valid player
            self.mock_get_player_name.return_value = "Jayden Daniels"
            self.mock_get_player_position.return_value = "QB"

            yield

    def test_creates_all_levels_for_new_entry(self):
        """Creates year, week, and manager levels when cache is empty."""
        update_starters_cache(2024, 1, "Tommy", "12345", 25.5)

        assert "2024" in self.mock_starters_cache
        assert "1" in self.mock_starters_cache["2024"]
        assert "Tommy" in self.mock_starters_cache["2024"]["1"]
        assert (
            "Jayden Daniels" in (self.mock_starters_cache["2024"]["1"]["Tommy"])
        )

    def test_adds_player_to_existing_manager(self):
        """Adds player to existing manager data."""
        self.mock_starters_cache["2024"] = {
            "1": {
                "Tommy": {
                    "Total_Points": 10.0,
                    "Patrick Mahomes": {
                        "points": 10.0,
                        "position": "QB",
                        "player_id": "4046",
                    },
                }
            }
        }

        self.mock_get_player_name.return_value = "Saquon Barkley"
        self.mock_get_player_position.return_value = "RB"

        update_starters_cache(2024, 1, "Tommy", "5678", 15.5)

        manager_data = self.mock_starters_cache["2024"]["1"]["Tommy"]
        assert "Saquon Barkley" in manager_data
        assert manager_data["Saquon Barkley"]["points"] == 15.5
        assert manager_data["Saquon Barkley"]["position"] == "RB"
        assert manager_data["Saquon Barkley"]["player_id"] == "5678"
        assert manager_data["Total_Points"] == 25.5

    def test_creates_week_under_existing_year(self):
        """Creates week level when year already exists."""
        self.mock_starters_cache["2024"] = {}

        update_starters_cache(2024, 2, "Tommy", "12345", 20.0)

        assert "2" in self.mock_starters_cache["2024"]
        assert "Tommy" in self.mock_starters_cache["2024"]["2"]

    def test_creates_manager_under_existing_week(self):
        """Creates manager level when year and week already exist."""
        self.mock_starters_cache["2024"] = {"1": {}}

        update_starters_cache(2024, 1, "Tommy", "12345", 18.0)

        assert "Tommy" in self.mock_starters_cache["2024"]["1"]

    def test_returns_early_when_player_name_not_found(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Logs warning and returns when player name not found.

        Args:
            caplog: pytest log capture fixture.
        """
        self.mock_get_player_name.return_value = None

        update_starters_cache(2024, 1, "Tommy", "99999", 10.0)

        assert "Unknown player: 99999" in caplog.text
        # Manager data should have Total_Points but no player
        manager_data = self.mock_starters_cache["2024"]["1"]["Tommy"]
        assert manager_data == {"Total_Points": 0.0}

    def test_returns_early_when_position_not_found(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Logs warning and returns when player position not found.

        Args:
            caplog: pytest log capture fixture.
        """
        self.mock_get_player_position.return_value = None

        update_starters_cache(2024, 1, "Tommy", "99999", 10.0)

        assert "Unknown player: 99999" in caplog.text
        manager_data = self.mock_starters_cache["2024"]["1"]["Tommy"]
        assert manager_data == {"Total_Points": 0.0}

    def test_returns_early_for_duplicate_player(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Logs warning and returns when player already exists.

        Args:
            caplog: pytest log capture fixture.
        """
        self.mock_starters_cache["2024"] = {
            "1": {
                "Tommy": {
                    "Total_Points": 25.5,
                    "Jayden Daniels": {
                        "points": 25.5,
                        "position": "QB",
                        "player_id": "12345",
                    },
                }
            }
        }

        update_starters_cache(2024, 1, "Tommy", "12345", 30.0)

        assert "Duplicate player: Jayden Daniels" in caplog.text
        # Total points should not change
        assert (
            self.mock_starters_cache["2024"]["1"]["Tommy"]["Total_Points"]
            == 25.5
        )

    def test_total_points_calculation_with_decimal_precision(self):
        """Calculates total points with proper decimal precision."""
        self.mock_starters_cache["2024"] = {
            "1": {
                "Tommy": {
                    "Total_Points": 10.33,
                }
            }
        }

        update_starters_cache(2024, 1, "Tommy", "12345", 5.67)

        # 10.33 + 5.67 = 16.00, normalized to 16
        assert (
            self.mock_starters_cache["2024"]["1"]["Tommy"]["Total_Points"] == 16
        )

    def test_total_points_rounds_to_two_decimal_places(self):
        """Rounds total points to two decimal places."""
        self.mock_starters_cache["2024"] = {
            "1": {
                "Tommy": {
                    "Total_Points": 10.111,
                }
            }
        }

        update_starters_cache(2024, 1, "Tommy", "12345", 5.222)

        # 10.111 + 5.222 = 15.333, rounded to 15.33
        assert (
            self.mock_starters_cache["2024"]["1"]["Tommy"]["Total_Points"]
            == 15.33
        )

    def test_player_data_structure(self):
        """Verifies correct player data structure is created."""
        update_starters_cache(2024, 1, "Tommy", "12345", 22.75)

        player_data = (
            self.mock_starters_cache["2024"]["1"]["Tommy"]["Jayden Daniels"]
        )
        assert player_data == {
            "points": 22.75,
            "position": "QB",
            "player_id": "12345",
        }

    def test_initializes_total_points_to_zero(self):
        """Initializes Total_Points to 0.0 for new manager."""
        self.mock_get_player_name.return_value = None  # Force early return

        update_starters_cache(2024, 1, "Tommy", "99999", 10.0)

        assert (
            self.mock_starters_cache["2024"]["1"]["Tommy"]["Total_Points"]
            == 0.0
        )
