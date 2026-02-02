"""Unit tests for starters_exporter module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.exporters.starters_exporter import (
    get_starters,
)

MODULE_PATH = "patriot_center_backend.exporters.starters_exporter"


class TestGetStarters:
    """Test get_starters method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `get_starters_from_cache`: `mock_get_starters_from_cache`

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.get_starters_from_cache"
            ) as mock_get_starters_from_cache,
        ):
            self.mock_get_starters_from_cache = mock_get_starters_from_cache
            self.mock_get_starters_from_cache.return_value = {}

            yield

    def test_get_starters_no_filters(self):
        """Test getting all starters with no filters."""
        self.mock_get_starters_from_cache.return_value = {
            "2023": {"1": {"Tommy": {"Jayden Daniels": {"points": 20.5}}}}
        }

        result = get_starters()

        assert "2023" in result
        self.mock_get_starters_from_cache.assert_called_once_with(
            None, None, None
        )

    def test_get_starters_with_season(self):
        """Test getting starters filtered by season."""
        get_starters(season=2023)

        self.mock_get_starters_from_cache.assert_called_once_with(
            None, 2023, None
        )

    def test_get_starters_with_week(self):
        """Test getting starters filtered by week."""
        get_starters(week=5)

        self.mock_get_starters_from_cache.assert_called_once_with(
            None, None, 5
        )

    def test_get_starters_with_manager(self):
        """Test getting starters filtered by manager."""
        get_starters(manager="Tommy")

        self.mock_get_starters_from_cache.assert_called_once_with(
            "Tommy", None, None
        )

    def test_get_starters_with_all_filters(self):
        """Test getting starters with all filters applied."""
        get_starters(manager="Tommy", season=2023, week=5)

        self.mock_get_starters_from_cache.assert_called_once_with(
            "Tommy", 2023, 5
        )

    def test_get_starters_empty_result(self):
        """Test getting starters when cache returns empty."""
        self.mock_get_starters_from_cache.return_value = {}

        result = get_starters()

        assert result == {}
