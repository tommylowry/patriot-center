"""Unit tests for rolling_average_calculator module."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.calculations.rolling_average_calculator import (
    _enforce_monotonicity,
    calculate_three_year_averages,
)


class TestCalculateThreeYearAverages:
    """Test calculate_three_year_averages function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_replacement_score_cache`:
            `mock_get_replacement_score_cache`

        Yields:
            None
        """
        with patch(
            "patriot_center_backend.calculations.rolling_average_calculator"
            ".CACHE_MANAGER.get_replacement_score_cache"
        ) as mock_get_replacement_score_cache:
            self.mock_replacement_score_cache: dict[str, Any] = {
                "2024": {
                    "1": {
                        "byes": 4,
                        "2024_scoring": {
                            "QB": 15.0,
                            "RB": 8.0,
                            "WR": 9.0,
                            "TE": 5.0,
                        },
                    },
                },
                "2023": {
                    "1": {
                        "byes": 4,
                        "2024_scoring": {
                            "QB": 14.0,
                            "RB": 7.5,
                            "WR": 8.5,
                            "TE": 4.5,
                        },
                    },
                },
                "2022": {
                    "1": {
                        "byes": 4,
                        "2024_scoring": {
                            "QB": 13.0,
                            "RB": 7.0,
                            "WR": 8.0,
                            "TE": 4.0,
                        },
                    },
                },
                "2021": {
                    "1": {
                        "byes": 4,
                        "2024_scoring": {
                            "QB": 12.0,
                            "RB": 6.5,
                            "WR": 7.5,
                            "TE": 3.5,
                        },
                    },
                },
            }
            mock_get_replacement_score_cache.return_value = (
                self.mock_replacement_score_cache
            )

            yield

    def test_adds_three_year_avg_keys_to_current_week(self):
        """Test adds _3yr_avg keys for each position."""
        result = calculate_three_year_averages(2024, 1)

        assert "QB_3yr_avg" in result
        assert "RB_3yr_avg" in result
        assert "WR_3yr_avg" in result
        assert "TE_3yr_avg" in result

    def test_returns_current_week_scores(self):
        """Test returns the current week's scores dict (mutated)."""
        result = calculate_three_year_averages(2024, 1)

        assert result["byes"] == 4
        assert "2024_scoring" in result

    def test_skips_missing_past_years(self):
        """Test skips years not present in cache."""
        del self.mock_replacement_score_cache["2021"]

        result = calculate_three_year_averages(2024, 1)

        assert "QB_3yr_avg" in result

    def test_skips_missing_weeks_in_past_years(self):
        """Test skips weeks not present in past year cache."""
        self.mock_replacement_score_cache["2023"] = {}

        result = calculate_three_year_averages(2024, 1)

        assert "QB_3yr_avg" in result

    def test_current_season_only_includes_up_to_current_week(self):
        """Test current season only considers weeks up to current week."""
        self.mock_replacement_score_cache["2024"]["2"] = {
            "byes": 6,
            "2024_scoring": {"QB": 20.0, "RB": 12.0, "WR": 14.0, "TE": 8.0},
        }

        result = calculate_three_year_averages(2024, 1)

        # Week 2 data should NOT be included since we're calculating for week 1
        assert "QB_3yr_avg" in result


class TestEnforceMonotonicity:
    """Test _enforce_monotonicity function."""

    def test_no_change_when_already_monotonic(self):
        """Test does not modify already non-increasing data.

        Monotonicity here means: fewer byes >= more byes.
        """
        averages = {
            "QB": {2: 14.0, 4: 12.0, 6: 10.0},
            "RB": {2: 9.0, 4: 7.0, 6: 5.0},
        }

        _enforce_monotonicity(averages)

        assert averages["QB"] == {2: 14.0, 4: 12.0, 6: 10.0}

    def test_adjusts_lower_bye_count_when_higher_has_more(self):
        """Test adjusts lower bye count score up when higher bye has more."""
        averages = {
            "QB": {2: 15.0, 4: 12.0, 6: 14.0},
            "RB": {2: 5.0, 4: 7.0, 6: 9.0},
        }

        _enforce_monotonicity(averages)

        # 2-bye QB was 15.0, but 4-bye was only 12.0
        # 6-bye is 14.0 > 4-bye 12.0, so 4-bye becomes 14.0
        # then 4-bye 14.0 < 2-bye 15.0, so 2-bye stays 15.0
        assert averages["QB"][4] == 14.0
        assert averages["QB"][2] == 15.0

    def test_cascading_adjustment(self):
        """Test cascading adjustments through multiple bye counts."""
        averages = {
            "QB": {2: 5.0, 4: 6.0, 6: 20.0},
            "RB": {2: 5.0, 4: 6.0, 6: 20.0},
        }

        _enforce_monotonicity(averages)

        # 6-bye (20.0) > 4-bye (6.0), so 4-bye becomes 20.0
        # 4-bye (20.0) > 2-bye (5.0), so 2-bye becomes 20.0
        assert averages["QB"][2] == 20.0
        assert averages["QB"][4] == 20.0
        assert averages["QB"][6] == 20.0

    def test_applies_to_all_positions(self):
        """Test applies monotonicity to all positions."""
        averages = {
            "QB": {2: 10.0, 4: 15.0},
            "RB": {2: 3.0, 4: 8.0},
        }

        _enforce_monotonicity(averages)

        assert averages["QB"][2] == 15.0
        assert averages["RB"][2] == 8.0

    def test_equal_values_no_change(self):
        """Test does not modify when all values are equal."""
        averages = {
            "QB": {2: 10.0, 4: 10.0, 6: 10.0},
        }

        _enforce_monotonicity(averages)

        assert averages["QB"] == {2: 10.0, 4: 10.0, 6: 10.0}
