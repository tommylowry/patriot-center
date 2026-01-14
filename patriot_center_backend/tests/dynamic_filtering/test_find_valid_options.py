"""Unit tests for find_valid_options module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.dynamic_filtering.find_valid_options import (
    _get_weeks_to_check,
    find_valid_managers,
    find_valid_positions,
    find_valid_weeks,
    find_valid_years,
)


@pytest.fixture()
def mock_valid_options_cache():
    """Shared mock data for valid_options_cache used by all test classes.

    Structure mirrors the real cache: cache[year][week][manager][positions/players]
    """
    return {
        "2024": {
            "weeks": ["1", "2", "3"],
            "1": {
                "managers": ["Tommy"],
                "positions": ["QB"],
                "players": ["Josh Allen"],
                "Tommy": {
                    "positions": ["QB"],
                    "players": ["Josh Allen"]
                }
            },
            "2": {
                "managers": ["Anthony"],
                "positions": ["RB"],
                "players": ["Rico Dowdle"],
                "Anthony": {
                    "positions": ["RB"],
                    "players": ["Rico Dowdle"]
                }
            },
            "3": {
                "managers": ["Tommy", "Anthony"],
                "positions": ["QB", "RB"],
                "players": ["Josh Allen", "Rico Dowdle"],
                "Tommy": {
                    "positions": ["QB"],
                    "players": ["Josh Allen"]
                },
                "Anthony": {
                    "positions": ["RB"],
                    "players": ["Rico Dowdle"]
                }
            }
        },
        "2023": {
            "weeks": ["1", "2"],
            "1": {
                "managers": ["Owen"],
                "positions": ["WR"],
                "players": ["Amon-Ra St. Brown"],
                "Owen": {
                    "positions": ["WR"],
                    "players": ["Amon-Ra St. Brown"]
                }
            },
            "2": {
                "managers": ["Anthony"],
                "positions": ["RB"],
                "players": ["Rico Dowdle"],
                "Anthony": {
                    "positions": ["RB"],
                    "players": ["Rico Dowdle"]
                }
            }
        },
        "2022": {
            "weeks": ["1"],
            "1": {
                "managers": ["Anthony"],
                "positions": ["TE"],
                "players": ["George Kittle"],
                "Anthony": {
                    "positions": ["TE"],
                    "players": ["George Kittle"]
                }
            }
        }
    }


class TestFindValidYears:
    """Tests for find_valid_years function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_valid_options_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.find_valid_options.CACHE_MANAGER.get_valid_options_cache') as mock_get_valid_options_cache:

            self.mock_valid_options_cache = mock_valid_options_cache

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = self.mock_valid_options_cache

            yield

    # ===== No filters =====
    def test_returns_all_years_when_no_filters(self):
        """Returns all years when no filters are provided."""
        result = find_valid_years(
            manager=None,
            position=None,
            player=None
        )

        assert result == {"2024", "2023", "2022"}

    # ===== Single filter =====
    def test_filters_by_manager_only(self):
        """Returns only years where manager exists."""
        result = find_valid_years(
            manager="Tommy",
            position=None,
            player=None
        )

        assert result == {"2024"}

    def test_filters_by_position_only(self):
        """Returns only years where position exists."""
        result = find_valid_years(
            manager=None,
            position="QB",
            player=None
        )

        assert result == {"2024"}

    def test_filters_by_player_only(self):
        """Returns only years where player exists."""
        result = find_valid_years(
            manager=None,
            position=None,
            player="Josh Allen"
        )

        assert result == {"2024"}

    # ===== Two filters =====
    def test_filters_by_manager_and_position(self):
        """Returns only years matching manager AND position."""
        result = find_valid_years(
            manager="Anthony",
            position="RB",
            player=None
        )

        assert result == {"2024", "2023"}

    def test_filters_by_manager_and_player(self):
        """Returns only years matching manager AND player."""
        result = find_valid_years(
            manager="Anthony",
            position=None,
            player="Rico Dowdle"
        )

        assert result == {"2024", "2023"}

    def test_filters_by_position_and_player(self):
        """Returns only years matching position AND player."""
        result = find_valid_years(
            manager=None,
            position="QB",
            player="Josh Allen"
        )

        assert result == {"2024"}

    # ===== Three filters =====
    def test_filters_by_all_criteria(self):
        """Returns only years matching manager, position, AND player."""
        result = find_valid_years(
            manager="Tommy",
            position="QB",
            player="Josh Allen"
        )

        assert result == {"2024"}

    def test_filters_by_all_criteria_no_match(self, caplog):
        """Returns empty set when no year matches all filters."""
        result = find_valid_years(
            manager="Tommy",
            position="WR",
            player="Amon-Ra St. Brown"
        )

        assert "No valid years found" in caplog.text

        assert result == set()

    # ===== Edge cases =====
    def test_returns_empty_set_when_no_matches(self, caplog):
        """Returns empty set when no years match filters."""
        result = find_valid_years(
            manager="Owen",
            position="QB",
            player=None
        )

        assert "No valid years found" in caplog.text

        assert result == set()


class TestFindValidWeeks:
    """Tests for find_valid_weeks function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_valid_options_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.find_valid_options.CACHE_MANAGER.get_valid_options_cache') as mock_get_valid_options_cache:

            self.mock_valid_options_cache = mock_valid_options_cache

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = self.mock_valid_options_cache

            yield

    # ===== No filters (except year) =====
    def test_returns_all_weeks_for_year(self):
        """Returns all weeks for specified year when no other filters."""
        result = find_valid_weeks(
            year="2024",
            manager=None,
            position=None,
            player=None
        )

        assert result == {"1", "2", "3"}

    def test_returns_weeks_across_all_years_when_no_year(self):
        """Returns weeks from all years when year not specified."""
        result = find_valid_weeks(
            year=None,
            manager=None,
            position=None,
            player=None
        )

        assert result == {"1", "2", "3"}

    # ===== Single filter (with year) =====
    def test_filters_by_year_and_manager(self):
        """Returns only weeks where manager exists in specified year."""
        result = find_valid_weeks(
            year="2024",
            manager="Tommy",
            position=None,
            player=None
        )

        assert result == {"1", "3"}

    def test_filters_by_year_and_position(self):
        """Returns only weeks where position exists in specified year."""
        result = find_valid_weeks(
            year="2024",
            manager=None,
            position="QB",
            player=None
        )

        assert result == {"1", "3"}

    def test_filters_by_year_and_player(self):
        """Returns only weeks where player exists in specified year."""
        result = find_valid_weeks(
            year="2024",
            manager=None,
            position=None,
            player="Josh Allen"
        )

        assert result == {"1", "3"}

    # ===== Single filter (no year) =====
    def test_filters_by_manager_across_all_years(self):
        """Returns weeks where manager exists across all years."""
        result = find_valid_weeks(
            year=None,
            manager="Owen",
            position=None,
            player=None
        )

        assert result == {"1"}

    def test_filters_by_position_across_all_years(self):
        """Returns weeks where position exists across all years."""
        result = find_valid_weeks(
            year=None,
            manager=None,
            position="WR",
            player=None
        )

        assert result == {"1"}

    def test_filters_by_player_across_all_years(self):
        """Returns weeks where player exists across all years."""
        result = find_valid_weeks(
            year=None,
            manager=None,
            position=None,
            player="Amon-Ra St. Brown"
        )

        assert result == {"1"}

    # ===== Two filters (with year) =====
    def test_filters_by_year_manager_and_position(self):
        """Returns weeks matching year, manager, AND position."""
        result = find_valid_weeks(
            year="2024",
            manager="Tommy",
            position="QB",
            player=None
        )

        assert result == {"1", "3"}

    def test_filters_by_year_manager_and_player(self):
        """Returns weeks matching year, manager, AND player."""
        result = find_valid_weeks(
            year="2024",
            manager="Tommy",
            position=None,
            player="Josh Allen"
        )

        assert result == {"1", "3"}

    def test_filters_by_year_position_and_player(self):
        """Returns weeks matching year, position, AND player."""
        result = find_valid_weeks(
            year="2024",
            manager=None,
            position="QB",
            player="Josh Allen"
        )

        assert result == {"1", "3"}

    # ===== Two filters (no year) =====
    def test_filters_by_manager_and_position_across_years(self):
        """Returns weeks matching manager AND position across all years."""
        result = find_valid_weeks(
            year=None,
            manager="Anthony",
            position="RB",
            player=None
        )

        assert result == {"2", "3"}

    def test_filters_by_manager_and_player_across_years(self):
        """Returns weeks matching manager AND player across all years."""
        result = find_valid_weeks(
            year=None,
            manager="Anthony",
            position=None,
            player="Rico Dowdle"
        )

        assert result == {"2", "3"}

    def test_filters_by_position_and_player_across_years(self):
        """Returns weeks matching position AND player across all years."""
        result = find_valid_weeks(
            year=None,
            manager=None,
            position="RB",
            player="Rico Dowdle"
        )

        assert result == {"2", "3"}

    # ===== Three filters =====
    def test_filters_by_year_manager_position_and_player(self):
        """Returns weeks matching all four filters."""
        result = find_valid_weeks(
            year="2024",
            manager="Tommy",
            position="QB",
            player="Josh Allen"
        )

        assert result == {"1", "3"}

    def test_filters_by_manager_position_and_player_across_years(self):
        """Returns weeks matching manager, position, AND player across years."""
        result = find_valid_weeks(
            year=None,
            manager="Anthony",
            position="RB",
            player="Rico Dowdle"
        )

        assert result == {"2", "3"}

    # ===== Edge cases =====
    def test_returns_empty_set_when_no_matches(self, caplog):
        """Returns empty set when no weeks match filters."""
        result = find_valid_weeks(
            year="2024",
            manager="Owen",
            position=None,
            player=None
        )

        assert "No valid weeks found" in caplog.text

        assert result == set()


class TestFindValidManagers:
    """Tests for find_valid_managers function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_valid_options_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.find_valid_options.CACHE_MANAGER.get_valid_options_cache') as mock_get_valid_options_cache, \
             patch('patriot_center_backend.dynamic_filtering.find_valid_options._get_weeks_to_check') as mock_get_weeks_to_check:

            self.mock_valid_options_cache = mock_valid_options_cache

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = self.mock_valid_options_cache

            self.mock_get_weeks_to_check = mock_get_weeks_to_check
            self.mock_get_weeks_to_check.return_value = ["1", "2"]

            yield

    # ===== No filters (except year/week) =====
    def test_returns_all_managers_for_year_and_week(self):
        """Returns all managers for specified year and week."""
        self.mock_get_weeks_to_check.return_value = ["1"]

        result = find_valid_managers(
            year="2024",
            week="1",
            position=None,
            player=None
        )

        assert result == {"Tommy"}

    def test_returns_all_managers_for_year_across_weeks(self):
        """Returns all managers for specified year across all weeks."""
        result = find_valid_managers(
            year="2024",
            week=None,
            position=None,
            player=None
        )

        assert result == {"Tommy", "Anthony"}

    def test_returns_all_managers_across_all_years_and_weeks(self):
        """Returns all managers when no year or week specified."""
        self.mock_get_weeks_to_check.return_value = []

        result = find_valid_managers(
            year=None,
            week=None,
            position=None,
            player=None
        )

        assert result == {"Tommy", "Anthony", "Owen"}

    # ===== Single filter =====
    def test_filters_by_position_only(self):
        """Returns managers with specified position."""
        self.mock_get_weeks_to_check.return_value = ["1"]

        result = find_valid_managers(
            year="2024",
            week="1",
            position="QB",
            player=None
        )

        assert result == {"Tommy"}

    def test_filters_by_player_only(self):
        """Returns managers with specified player."""
        self.mock_get_weeks_to_check.return_value = ["1"]

        result = find_valid_managers(
            year="2024",
            week="1",
            position=None,
            player="Josh Allen"
        )

        assert result == {"Tommy"}

    # ===== Two filters =====
    def test_filters_by_position_and_player(self):
        """Returns managers matching position AND player."""
        self.mock_get_weeks_to_check.return_value = ["1"]

        result = find_valid_managers(
            year="2024",
            week="1",
            position="QB",
            player="Josh Allen"
        )

        assert result == {"Tommy"}

    def test_filters_by_position_across_weeks(self):
        """Returns managers with position across all weeks."""
        result = find_valid_managers(
            year="2024",
            week=None,
            position="QB",
            player=None
        )

        assert result == {"Tommy"}

    def test_filters_by_player_across_weeks(self):
        """Returns managers with player across all weeks."""
        result = find_valid_managers(
            year="2024",
            week=None,
            position=None,
            player="Josh Allen"
        )

        assert result == {"Tommy"}

    # ===== Edge cases =====
    def test_returns_empty_set_when_no_matches(self, caplog):
        """Returns empty set when no managers match filters."""
        self.mock_get_weeks_to_check.return_value = ["1"]

        result = find_valid_managers(
            year="2024",
            week="1",
            position="K",
            player=None
        )

        assert "No valid managers found" in caplog.text

        assert result == set()


class TestFindValidPositions:
    """Tests for find_valid_positions function."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_valid_options_cache):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.find_valid_options.CACHE_MANAGER.get_valid_options_cache') as mock_get_valid_options_cache, \
             patch('patriot_center_backend.dynamic_filtering.find_valid_options._get_weeks_to_check') as mock_get_weeks_to_check:

            self.mock_valid_options_cache = mock_valid_options_cache

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = self.mock_valid_options_cache

            self.mock_get_weeks_to_check = mock_get_weeks_to_check
            self.mock_get_weeks_to_check.return_value = ["1", "2"]

            yield

    # ===== No manager filter =====
    def test_returns_all_positions_for_year_and_week(self):
        """Returns all positions for specified year and week."""
        self.mock_get_weeks_to_check.return_value = ["1"]

        result = find_valid_positions(
            year="2024",
            week="1",
            manager=None
        )

        assert result == {"QB"}

    def test_returns_all_positions_for_year_across_weeks(self):
        """Returns all positions for specified year across all weeks."""
        result = find_valid_positions(
            year="2024",
            week=None,
            manager=None
        )

        assert result == {"QB", "RB"}

    def test_returns_all_positions_across_all_years_and_weeks(self):
        """Returns all positions when no year or week specified."""
        self.mock_get_weeks_to_check.return_value = []

        result = find_valid_positions(
            year=None,
            week=None,
            manager=None
        )

        assert result == {"QB", "RB", "WR", "TE"}

    # ===== With manager filter =====
    def test_filters_by_manager_for_year_and_week(self):
        """Returns positions for specified manager in year and week."""
        self.mock_get_weeks_to_check.return_value = ["1"]

        result = find_valid_positions(
            year="2024",
            week="1",
            manager="Tommy"
        )

        assert result == {"QB"}

    def test_filters_by_manager_across_weeks(self):
        """Returns positions for manager across all weeks in year."""
        result = find_valid_positions(
            year="2024",
            week=None,
            manager="Tommy"
        )

        assert result == {"QB"}

    def test_filters_by_manager_across_years(self):
        """Returns positions for manager across all years."""
        self.mock_get_weeks_to_check.return_value = []

        result = find_valid_positions(
            year=None,
            week=None,
            manager="Anthony"
        )

        assert result == {"RB", "TE"}

    # ===== Edge cases =====
    def test_returns_empty_set_when_no_matches(self, caplog):
        """Returns empty set when no positions match filters."""
        self.mock_get_weeks_to_check.return_value = ["1"]

        result = find_valid_positions(
            year="2024",
            week="1",
            manager="Owen"
        )

        assert "No valid positions found" in caplog.text

        assert result == set()


class TestGetWeeksToCheck:
    """Tests for _get_weeks_to_check helper function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.find_valid_options.CACHE_MANAGER.get_valid_options_cache') as mock_get_valid_options_cache:

            self.mock_valid_options_cache = {
                "2024": {"weeks": ["1", "2", "3"]},
                "2023": {"weeks": ["1", "2"]}
            }

            self.mock_get_valid_options_cache = mock_get_valid_options_cache
            self.mock_get_valid_options_cache.return_value = self.mock_valid_options_cache

            yield

    def test_returns_single_week_when_week_provided(self):
        """Returns list with single week when week is provided."""
        result = _get_weeks_to_check(year="2024", week="5")

        assert result == ["5"]

    def test_returns_all_weeks_for_year_when_no_week(self):
        """Returns all weeks for year when week not provided."""
        result = _get_weeks_to_check(year="2024", week=None)

        assert result == ["1", "2", "3"]

    def test_returns_empty_list_when_no_year_or_week(self):
        """Returns empty list when neither year nor week provided."""
        result = _get_weeks_to_check(year=None, week=None)

        assert result == []

    def test_week_takes_precedence_over_year(self):
        """Week filter takes precedence even when year is provided."""
        result = _get_weeks_to_check(year="2024", week="2")

        assert result == ["2"]

    def test_returns_weeks_for_different_year(self):
        """Returns correct weeks for a different year."""
        result = _get_weeks_to_check(year="2023", week=None)

        assert result == ["1", "2"]
