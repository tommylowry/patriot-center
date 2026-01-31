"""Unit tests for _progress_tracker module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters._progress_tracker import (
    _get_last_updated,
    get_league_status,
    set_last_updated,
)


class TestGetLeagueStatus:
    """Test get_league_status function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `_get_last_updated`: `mock_get_last_updated`
        - `get_league_info`: `mock_get_league_info`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters._progress_tracker"
                "._get_last_updated"
            ) as mock_get_last_updated,
            patch(
                "patriot_center_backend.cache.updaters._progress_tracker"
                ".get_league_info"
            ) as mock_get_league_info,
        ):
            self.mock_get_last_updated = mock_get_last_updated
            self.mock_get_last_updated.return_value = (2024, 5)

            self.mock_get_league_info = mock_get_league_info
            self.mock_get_league_info.return_value = {
                "settings": {"last_scored_leg": 10},
                "status": "in_season",
            }

            yield

    def test_returns_weeks_to_update_for_current_year(self):
        """Test returns correct weeks when current year needs updating."""
        weeks, season_complete = get_league_status(2024)

        assert weeks == [6, 7, 8, 9, 10]
        assert season_complete is False

    def test_returns_empty_list_when_year_already_finished(self):
        """Test returns empty list when year is before last updated year."""
        weeks, _ = get_league_status(2023)

        assert weeks == []

    def test_returns_full_range_for_new_year(self):
        """Test returns weeks 1 through current for a new year."""
        self.mock_get_league_info.return_value = {
            "settings": {"last_scored_leg": 3},
            "status": "in_season",
        }

        weeks, _ = get_league_status(2025)

        assert weeks == [1, 2, 3]

    def test_returns_empty_list_when_week_up_to_date(self):
        """Test returns empty list when already up to date."""
        self.mock_get_league_info.return_value = {
            "settings": {"last_scored_leg": 5},
            "status": "in_season",
        }

        weeks, _ = get_league_status(2024)

        assert weeks == []

    def test_season_complete_flag(self):
        """Test season_complete flag when status is complete."""
        self.mock_get_league_info.return_value = {
            "settings": {"last_scored_leg": 17},
            "status": "complete",
        }

        _, season_complete = get_league_status(2024)

        assert season_complete is True

    def test_returns_empty_when_week_less_than_last_updated(self):
        """Test returns empty when API week is less than last updated."""
        self.mock_get_league_info.return_value = {
            "settings": {"last_scored_leg": 3},
            "status": "in_season",
        }

        weeks, _ = get_league_status(2024)

        assert weeks == []


class TestSetLastUpdated:
    """Test set_last_updated function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_weekly_data_progress_tracker`:
            `mock_get_progress`

        Yields:
            None
        """
        with patch(
            "patriot_center_backend.cache.updaters._progress_tracker"
            ".CACHE_MANAGER.get_weekly_data_progress_tracker"
        ) as mock_get_progress:
            self.mock_progress_data = {}
            mock_get_progress.return_value = self.mock_progress_data

            yield

    def test_sets_year_and_week(self):
        """Test sets year and week in progress tracker."""
        set_last_updated(2024, 10)

        assert self.mock_progress_data["year"] == 2024
        assert self.mock_progress_data["week"] == 10

    def test_overwrites_existing_values(self):
        """Test overwrites existing year and week values."""
        self.mock_progress_data["year"] = 2023
        self.mock_progress_data["week"] = 5

        set_last_updated(2024, 1)

        assert self.mock_progress_data["year"] == 2024
        assert self.mock_progress_data["week"] == 1


class TestGetLastUpdated:
    """Test _get_last_updated function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_weekly_data_progress_tracker`:
            `mock_get_progress`

        Yields:
            None
        """
        with patch(
            "patriot_center_backend.cache.updaters._progress_tracker"
            ".CACHE_MANAGER.get_weekly_data_progress_tracker"
        ) as mock_get_progress:
            self.mock_progress_data = {"year": 2024, "week": 10}
            mock_get_progress.return_value = self.mock_progress_data

            yield

    def test_returns_year_and_week(self):
        """Test returns the stored year and week."""
        year, week = _get_last_updated()

        assert year == 2024
        assert week == 10

    def test_returns_zeros_when_empty(self):
        """Test returns (0, 0) when progress tracker is empty."""
        self.mock_progress_data.clear()

        year, week = _get_last_updated()

        assert year == 0
        assert week == 0
