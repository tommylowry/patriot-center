"""Unit tests for formatter module."""

from unittest.mock import patch

import pytest

from patriot_center_backend.dynamic_filtering.formatter import (
    format_output,
    format_positions,
    format_weeks,
)


class TestFormatOutput:
    """Tests for format_output function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests."""
        with patch('patriot_center_backend.dynamic_filtering.formatter.format_weeks') as mock_format_weeks, \
             patch('patriot_center_backend.dynamic_filtering.formatter.format_positions') as mock_format_positions:

            self.mock_format_weeks = mock_format_weeks
            self.mock_format_positions = mock_format_positions

            self.mock_format_weeks.return_value = ["1", "2", "10"]
            self.mock_format_positions.return_value = ["QB", "RB"]

            yield

    def test_formats_all_fields_correctly(self):
        """Formats years, weeks, managers, and positions correctly."""
        result = format_output(years={"2023", "2024"},
                               weeks={"1", "2", "10"},
                               managers={"Tommy", "Anthony"},
                               positions={"QB", "RB"})

        assert result["years"] == ["2024", "2023"]  # reverse sorted
        assert result["weeks"] == ["1", "2", "10"]  # from mock
        assert result["managers"] == ["Anthony",
                                      "Tommy"]  # alphabetically sorted
        assert result["positions"] == ["QB", "RB"]  # from mock

    def test_calls_format_weeks_with_weeks(self):
        """Calls format_weeks with the weeks set."""
        format_output(years={"2024"},
                      weeks={"1", "2"},
                      managers={"Tommy"},
                      positions={"QB"})

        self.mock_format_weeks.assert_called_once_with({"1", "2"})

    def test_calls_format_positions_with_positions(self):
        """Calls format_positions with the positions set."""
        format_output(years={"2024"},
                      weeks={"1"},
                      managers={"Tommy"},
                      positions={"QB", "RB"})

        self.mock_format_positions.assert_called_once_with({"QB", "RB"})

    def test_handles_empty_sets(self):
        """Handles empty sets correctly."""
        self.mock_format_weeks.return_value = []
        self.mock_format_positions.return_value = []

        result = format_output(years=set(),
                               weeks=set(),
                               managers=set(),
                               positions=set())

        assert result["years"] == []
        assert result["weeks"] == []
        assert result["managers"] == []
        assert result["positions"] == []

    def test_handles_single_item_sets(self):
        """Handles single item sets correctly."""
        self.mock_format_weeks.return_value = ["1"]
        self.mock_format_positions.return_value = ["QB"]

        result = format_output(years={"2024"},
                               weeks={"1"},
                               managers={"Tommy"},
                               positions={"QB"})

        assert result["years"] == ["2024"]
        assert result["weeks"] == ["1"]
        assert result["managers"] == ["Tommy"]
        assert result["positions"] == ["QB"]


class TestFormatWeeks:
    """Tests for format_weeks function."""

    def test_sorts_weeks_numerically(self):
        """Sorts weeks numerically, not lexicographically."""
        result = format_weeks({"1", "2", "10", "9"})

        assert result == ["1", "2", "9", "10"]

    def test_handles_empty_set(self):
        """Handles empty set correctly."""
        result = format_weeks(set())

        assert result == []

    def test_handles_single_week(self):
        """Handles single week correctly."""
        result = format_weeks({"5"})

        assert result == ["5"]

    def test_returns_strings(self):
        """Returns list of strings, not integers."""
        result = format_weeks({"1", "2"})

        assert all(isinstance(w, str) for w in result)


class TestFormatPositions:
    """Tests for format_positions function."""

    def test_sorts_positions_in_correct_order(self):
        """Sorts positions in order: QB, RB, WR, TE, K, DEF."""
        result = format_positions({"DEF", "QB", "WR", "RB", "K", "TE"})

        assert result == ["QB", "RB", "WR", "TE", "K", "DEF"]

    def test_handles_subset_of_positions(self):
        """Handles subset of positions correctly."""
        result = format_positions({"WR", "QB"})

        assert result == ["QB", "WR"]

    def test_handles_empty_set(self):
        """Handles empty set correctly."""
        result = format_positions(set())

        assert result == []

    def test_handles_single_position(self):
        """Handles single position correctly."""
        result = format_positions({"TE"})

        assert result == ["TE"]

    def test_filters_out_invalid_positions(self):
        """Filters out positions not in the desired order list."""
        result = format_positions({"QB", "INVALID", "RB"})

        assert result == ["QB", "RB"]
        assert "INVALID" not in result
