"""Unit tests for starters_queries module."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.queries.starters_queries import (
    get_starters_from_cache,
)

MODULE_PATH = "patriot_center_backend.cache.queries.starters_queries"


@pytest.fixture
def mock_starters_cache() -> dict[str, Any]:
    """Create a sample starters cache for testing.

    Returns:
        Sample starters cache.
    """
    return {
        "Last_Updated_Season": "2023",
        "Last_Updated_Week": "5",
        "2023": {
            "1": {
                "Tommy": {
                    "Jayden Daniels": {
                        "points": 25.5,
                        "position": "QB",
                    },
                    "Total_Points": 120.0,
                },
                "Benz": {
                    "Brian Robinson": {
                        "points": 15.0,
                        "position": "RB",
                    },
                    "Total_Points": 100.0,
                },
            },
            "2": {
                "Tommy": {
                    "Jayden Daniels": {
                        "points": 30.0,
                        "position": "QB",
                    },
                    "Total_Points": 130.0,
                },
            },
        },
        "2022": {
            "1": {
                "Tommy": {
                    "Terry McLaurin": {
                        "points": 18.0,
                        "position": "WR",
                    },
                    "Total_Points": 95.0,
                },
            },
        },
    }


class TestGetStartersFromCache:
    """Test get_starters_from_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_starters_cache: dict[str, Any]):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_starters_cache`:
            `mock_get_starters_cache`

        Args:
            mock_starters_cache: A mock starters cache.

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_starters_cache"
            ) as mock_get_starters_cache,
        ):
            self.mock_starters_cache = mock_starters_cache

            mock_get_starters_cache.return_value = self.mock_starters_cache

            yield

    def test_no_filters_returns_full_cache(self):
        """Test returns full cache when no filters provided."""
        result = get_starters_from_cache()

        assert result == self.mock_starters_cache

    def test_filter_by_season_only(self):
        """Test filtering by season returns all weeks for that season."""
        result = get_starters_from_cache(season=2023)

        assert "2023" in result
        assert "2022" not in result
        assert "1" in result["2023"]
        assert "2" in result["2023"]

    def test_filter_by_season_and_week(self):
        """Test filtering by season and week returns single week."""
        result = get_starters_from_cache(season=2023, week=1)

        assert "2023" in result
        assert "1" in result["2023"]
        assert "2" not in result["2023"]

    def test_filter_by_manager_only(self):
        """Test filtering by manager returns all data for that manager."""
        result = get_starters_from_cache(manager="Tommy")

        # Should have both seasons
        assert "2023" in result
        assert "2022" in result
        # Should only have Tommy's data
        assert "Tommy" in result["2023"]["1"]
        assert "Benz" not in result["2023"]["1"]

    def test_filter_by_manager_and_season(self):
        """Test filtering by manager and season."""
        result = get_starters_from_cache(manager="Tommy", season=2023)

        assert "2023" in result
        assert "2022" not in result
        assert "Tommy" in result["2023"]["1"]

    def test_filter_by_manager_and_season_and_week(self):
        """Test filtering by manager, season, and week."""
        result = get_starters_from_cache(manager="Tommy", season=2023, week=1)

        assert "2023" in result
        assert "1" in result["2023"]
        assert "2" not in result["2023"]
        assert "Tommy" in result["2023"]["1"]

    def test_filter_by_season_not_in_cache(self):
        """Test filtering by non-existent season returns empty."""
        result = get_starters_from_cache(season=2020)

        assert result == {}

    def test_filter_by_season_and_week_not_in_cache(self):
        """Test filtering by non-existent week returns empty."""
        result = get_starters_from_cache(season=2023, week=10)

        assert result == {}

    def test_filter_by_manager_not_in_cache(self):
        """Test filtering by non-existent manager returns empty."""
        result = get_starters_from_cache(manager="NotAManager")

        assert result == {}

    def test_manager_filter_skips_metadata_keys(self):
        """Test manager filter skips Last_Updated_Season/Week keys."""
        result = get_starters_from_cache(manager="Tommy")

        assert "Last_Updated_Season" not in result
        assert "Last_Updated_Week" not in result
