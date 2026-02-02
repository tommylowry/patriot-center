"""Unit tests for argument_parser module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.utils.argument_parser import parse_arguments

MODULE_PATH = "patriot_center_backend.utils.argument_parser"


class TestParseArguments:
    """Test parse_arguments function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `LEAGUE_IDS`: mocked constant
        - `NAME_TO_MANAGER_USERNAME`: mocked constant

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2023: "979405891168493568"},
            ),
            patch(
                f"{MODULE_PATH}.NAME_TO_MANAGER_USERNAME",
                {
                    "Tommy": "tommylowry",
                    "Benz": "bbennick",
                },
            ),
        ):
            yield

    def test_all_none_returns_all_none(self):
        """Test all None arguments returns (None, None, None)."""
        year, week, manager = parse_arguments(None, None, None)

        assert year is None
        assert week is None
        assert manager is None

    def test_year_only(self):
        """Test parsing a valid year argument."""
        year, week, manager = parse_arguments("2023", None, None)

        assert year == 2023
        assert week is None
        assert manager is None

    def test_week_only_raises(self):
        """Test week without year raises ValueError."""
        with pytest.raises(ValueError, match="Week provided without"):
            parse_arguments("5", None, None)

    def test_manager_only(self):
        """Test parsing a valid manager argument."""
        year, week, manager = parse_arguments("Tommy", None, None)

        assert year is None
        assert week is None
        assert manager == "Tommy"

    def test_year_and_week(self):
        """Test parsing year and week together."""
        year, week, manager = parse_arguments("2023", "5", None)

        assert year == 2023
        assert week == 5
        assert manager is None

    def test_year_and_manager(self):
        """Test parsing year and manager together."""
        year, week, manager = parse_arguments("2023", "Tommy", None)

        assert year == 2023
        assert week is None
        assert manager == "Tommy"

    def test_all_three_arguments(self):
        """Test parsing year, week, and manager together."""
        year, week, manager = parse_arguments("2023", "5", "Tommy")

        assert year == 2023
        assert week == 5
        assert manager == "Tommy"

    def test_arguments_in_any_order(self):
        """Test arguments can be provided in any order."""
        year, week, manager = parse_arguments("Tommy", "5", "2023")

        assert year == 2023
        assert week == 5
        assert manager == "Tommy"

    def test_multiple_years_raises(self):
        """Test multiple year arguments raises ValueError."""
        with pytest.raises(ValueError, match="Multiple year"):
            parse_arguments("2023", "2023", None)

    def test_multiple_weeks_raises(self):
        """Test multiple week arguments raises ValueError."""
        with pytest.raises(ValueError, match="Multiple week"):
            parse_arguments("2023", "5", "10")

    def test_multiple_managers_raises(self):
        """Test multiple manager arguments raises ValueError."""
        with pytest.raises(ValueError, match="Multiple manager"):
            parse_arguments("Tommy", "Benz", None)

    def test_invalid_string_raises(self):
        """Test invalid string argument raises ValueError."""
        with pytest.raises(ValueError, match="Invalid argument"):
            parse_arguments("NotAManager", None, None)

    def test_invalid_integer_raises(self):
        """Test invalid integer (not year or week) raises ValueError."""
        with pytest.raises(ValueError, match="Invalid integer"):
            parse_arguments("9999", None, None)

    def test_week_boundary_low(self):
        """Test week=1 is valid with year."""
        _, week, _ = parse_arguments("2023", "1", None)

        assert week == 1

    def test_week_boundary_high(self):
        """Test week=17 is valid with year."""
        _, week, _ = parse_arguments("2023", "17", None)

        assert week == 17
