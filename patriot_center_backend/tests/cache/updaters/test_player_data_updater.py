"""Unit tests for player_data_updater module."""

from unittest.mock import MagicMock, patch

import pytest

from patriot_center_backend.cache.updaters.player_data_updater import (
    update_player_data_cache,
)


class TestUpdatePlayerDataCache:
    """Test update_player_data_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_data_cache`: `mock_get_player_data_cache`
        - `FFWARCalculator`: `mock_ffwar_calculator_class`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                ".CACHE_MANAGER.get_player_data_cache"
            ) as mock_get_player_data_cache,
            patch(
                "patriot_center_backend.cache.updaters.player_data_updater"
                ".FFWARCalculator"
            ) as mock_ffwar_calculator_class,
        ):
            self.mock_player_data_cache = {}
            mock_get_player_data_cache.return_value = (
                self.mock_player_data_cache
            )

            self.mock_calculator_instance = MagicMock()
            self.mock_calculator_instance.calculate_ffwar.return_value = {
                "4046": {
                    "name": "Patrick Mahomes",
                    "score": 25.0,
                    "ffWAR": 0.125,
                    "position": "QB",
                    "manager": "Tommy",
                    "started": True,
                },
            }
            mock_ffwar_calculator_class.return_value = (
                self.mock_calculator_instance
            )
            self.mock_ffwar_calculator_class = mock_ffwar_calculator_class

            yield

    def test_stores_result_in_cache(self):
        """Test stores ffWAR result in the player data cache."""
        update_player_data_cache(2024, 1)

        assert "2024" in self.mock_player_data_cache
        assert "1" in self.mock_player_data_cache["2024"]
        assert self.mock_player_data_cache["2024"]["1"]["4046"]["ffWAR"] == (
            0.125
        )

    def test_creates_year_key_if_missing(self):
        """Test creates year key via setdefault if missing."""
        update_player_data_cache(2024, 5)

        assert "2024" in self.mock_player_data_cache

    def test_preserves_existing_year_data(self):
        """Test preserves existing weeks when adding new week."""
        self.mock_player_data_cache["2024"] = {"1": {"existing": "data"}}

        update_player_data_cache(2024, 2)

        assert self.mock_player_data_cache["2024"]["1"] == {"existing": "data"}
        assert "2" in self.mock_player_data_cache["2024"]

    def test_instantiates_calculator_with_correct_args(self):
        """Test instantiates FFWARCalculator with year and week."""
        update_player_data_cache(2023, 10)

        self.mock_ffwar_calculator_class.assert_called_once_with(2023, 10)

    def test_calls_calculate_ffwar(self):
        """Test calls calculate_ffwar on the calculator instance."""
        update_player_data_cache(2024, 1)

        self.mock_calculator_instance.calculate_ffwar.assert_called_once()
