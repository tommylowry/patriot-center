"""Unit tests for valid_options_updater module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters.valid_options_updater import (
    _update_list,
    update_valid_options_cache,
)


class TestUpdateValidOptionsCache:
    """Test update_valid_options_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined set of values when
        accessed.
        - `CACHE_MANAGER.get_valid_options_cache`:
            `mock_get_valid_options_cache`
        - `get_player_name`: `mock_get_player_name`
        - `get_player_position`: `mock_get_player_position`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.valid_options_updater"
                ".CACHE_MANAGER.get_valid_options_cache"
            ) as mock_get_valid_options_cache,
            patch(
                "patriot_center_backend.cache.updaters.valid_options_updater"
                ".get_player_name"
            ) as mock_get_player_name,
            patch(
                "patriot_center_backend.cache.updaters.valid_options_updater"
                ".get_player_position"
            ) as mock_get_player_position,
        ):
            self.mock_valid_options_cache: dict = {}
            mock_get_valid_options_cache.return_value = (
                self.mock_valid_options_cache
            )

            self.mock_get_player_name = mock_get_player_name
            self.mock_get_player_position = mock_get_player_position

            # Default return values for valid player
            self.mock_get_player_name.return_value = "Jayden Daniels"
            self.mock_get_player_position.return_value = "QB"

            yield

    def test_creates_all_levels_for_new_entry(self):
        """Creates year, week, and manager levels when cache is empty."""
        update_valid_options_cache(2024, 1, "Tommy", "12345")

        # Year level
        assert "2024" in self.mock_valid_options_cache
        year_data = self.mock_valid_options_cache["2024"]
        assert "Tommy" in year_data["managers"]
        assert "Jayden Daniels" in year_data["players"]
        assert "1" in year_data["weeks"]
        assert "QB" in year_data["positions"]

        # Week level
        assert "1" in year_data
        week_data = year_data["1"]
        assert "Tommy" in week_data["managers"]
        assert "Jayden Daniels" in week_data["players"]
        assert "QB" in week_data["positions"]

        # Manager level
        assert "Tommy" in week_data
        manager_data = week_data["Tommy"]
        assert "Jayden Daniels" in manager_data["players"]
        assert "QB" in manager_data["positions"]

    def test_adds_to_existing_year_level(self):
        """Adds new data to existing year level lists."""
        self.mock_valid_options_cache["2024"] = {
            "managers": ["Jerry"],
            "players": ["Patrick Mahomes"],
            "weeks": ["1"],
            "positions": ["QB"],
            "1": {
                "managers": ["Jerry"],
                "players": ["Patrick Mahomes"],
                "positions": ["QB"],
                "Jerry": {
                    "players": ["Patrick Mahomes"],
                    "positions": ["QB"],
                },
            },
        }

        self.mock_get_player_name.return_value = "Saquon Barkley"
        self.mock_get_player_position.return_value = "RB"

        update_valid_options_cache(2024, 2, "Tommy", "5678")

        year_data = self.mock_valid_options_cache["2024"]
        assert "Tommy" in year_data["managers"]
        assert "Jerry" in year_data["managers"]
        assert "Saquon Barkley" in year_data["players"]
        assert "2" in year_data["weeks"]
        assert "RB" in year_data["positions"]

    def test_adds_to_existing_week_level(self):
        """Adds new data to existing week level lists."""
        self.mock_valid_options_cache["2024"] = {
            "managers": ["Jerry"],
            "players": ["Patrick Mahomes"],
            "weeks": ["1"],
            "positions": ["QB"],
            "1": {
                "managers": ["Jerry"],
                "players": ["Patrick Mahomes"],
                "positions": ["QB"],
                "Jerry": {
                    "players": ["Patrick Mahomes"],
                    "positions": ["QB"],
                },
            },
        }

        update_valid_options_cache(2024, 1, "Tommy", "12345")

        week_data = self.mock_valid_options_cache["2024"]["1"]
        assert "Tommy" in week_data["managers"]
        assert "Jerry" in week_data["managers"]
        assert "Jayden Daniels" in week_data["players"]

    def test_adds_to_existing_manager_level(self):
        """Adds new data to existing manager level lists."""
        self.mock_valid_options_cache["2024"] = {
            "managers": ["Tommy"],
            "players": ["Patrick Mahomes"],
            "weeks": ["1"],
            "positions": ["QB"],
            "1": {
                "managers": ["Tommy"],
                "players": ["Patrick Mahomes"],
                "positions": ["QB"],
                "Tommy": {
                    "players": ["Patrick Mahomes"],
                    "positions": ["QB"],
                },
            },
        }

        update_valid_options_cache(2024, 1, "Tommy", "12345")

        manager_data = self.mock_valid_options_cache["2024"]["1"]["Tommy"]
        assert "Jayden Daniels" in manager_data["players"]
        assert "Patrick Mahomes" in manager_data["players"]

    def test_returns_early_when_player_name_not_found(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Logs warning and returns when player name not found.

        Args:
            caplog: pytest log capture fixture.
        """
        self.mock_get_player_name.return_value = None

        update_valid_options_cache(2024, 1, "Tommy", "99999")

        assert (
            "Could not find player or position for player_id: 99999"
            in caplog.text
        )
        assert self.mock_valid_options_cache == {}

    def test_returns_early_when_position_not_found(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Logs warning and returns when player position not found.

        Args:
            caplog: pytest log capture fixture.
        """
        self.mock_get_player_position.return_value = None

        update_valid_options_cache(2024, 1, "Tommy", "99999")

        assert (
            "Could not find player or position for player_id: 99999"
            in caplog.text
        )
        assert self.mock_valid_options_cache == {}

    def test_does_not_add_duplicate_values_at_year_level(self):
        """Does not add duplicate values to year level lists."""
        self.mock_valid_options_cache["2024"] = {
            "managers": ["Tommy"],
            "players": ["Jayden Daniels"],
            "weeks": ["1"],
            "positions": ["QB"],
            "1": {
                "managers": ["Tommy"],
                "players": ["Jayden Daniels"],
                "positions": ["QB"],
                "Tommy": {
                    "players": ["Jayden Daniels"],
                    "positions": ["QB"],
                },
            },
        }

        update_valid_options_cache(2024, 1, "Tommy", "12345")

        year_data = self.mock_valid_options_cache["2024"]
        assert year_data["managers"].count("Tommy") == 1
        assert year_data["players"].count("Jayden Daniels") == 1
        assert year_data["weeks"].count("1") == 1
        assert year_data["positions"].count("QB") == 1

    def test_does_not_add_duplicate_values_at_week_level(self):
        """Does not add duplicate values to week level lists."""
        self.mock_valid_options_cache["2024"] = {
            "managers": ["Tommy"],
            "players": ["Jayden Daniels"],
            "weeks": ["1"],
            "positions": ["QB"],
            "1": {
                "managers": ["Tommy"],
                "players": ["Jayden Daniels"],
                "positions": ["QB"],
                "Tommy": {
                    "players": ["Jayden Daniels"],
                    "positions": ["QB"],
                },
            },
        }

        update_valid_options_cache(2024, 1, "Tommy", "12345")

        week_data = self.mock_valid_options_cache["2024"]["1"]
        assert week_data["managers"].count("Tommy") == 1
        assert week_data["players"].count("Jayden Daniels") == 1
        assert week_data["positions"].count("QB") == 1

    def test_does_not_add_duplicate_values_at_manager_level(self):
        """Does not add duplicate values to manager level lists."""
        self.mock_valid_options_cache["2024"] = {
            "managers": ["Tommy"],
            "players": ["Jayden Daniels"],
            "weeks": ["1"],
            "positions": ["QB"],
            "1": {
                "managers": ["Tommy"],
                "players": ["Jayden Daniels"],
                "positions": ["QB"],
                "Tommy": {
                    "players": ["Jayden Daniels"],
                    "positions": ["QB"],
                },
            },
        }

        update_valid_options_cache(2024, 1, "Tommy", "12345")

        manager_data = self.mock_valid_options_cache["2024"]["1"]["Tommy"]
        assert manager_data["players"].count("Jayden Daniels") == 1
        assert manager_data["positions"].count("QB") == 1


class TestUpdateList:
    """Test _update_list function."""

    def test_adds_new_value_to_list(self):
        """Adds value to list when not already present."""
        test_list = ["existing_value"]

        _update_list(test_list, "new_value")

        assert "new_value" in test_list
        assert len(test_list) == 2

    def test_does_not_add_duplicate_value(self):
        """Does not add value when already present in list."""
        test_list = ["existing_value"]

        _update_list(test_list, "existing_value")

        assert test_list.count("existing_value") == 1
        assert len(test_list) == 1

    def test_adds_to_empty_list(self):
        """Adds value to empty list."""
        test_list: list[str] = []

        _update_list(test_list, "first_value")

        assert test_list == ["first_value"]
