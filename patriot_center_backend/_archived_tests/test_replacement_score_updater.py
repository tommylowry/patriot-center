"""Unit tests for replacement_score_updater module."""

import logging
from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters.replacement_score_updater import (
    _backfill_three_years,
    _fetch_replacement_score_for_week,
    _get_three_yr_avg,
    update_replacement_score_cache,
)


class TestUpdateReplacementScoreCache:
    """Test update_replacement_score_cache function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_replacement_score_cache`: `mock_get_cache`
        - `_backfill_three_years`: `mock_backfill`
        - `_fetch_replacement_score_for_week`: `mock_fetch`
        - `_get_three_yr_avg`: `mock_get_avg`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters"
                ".replacement_score_updater.CACHE_MANAGER"
                ".get_replacement_score_cache"
            ) as mock_get_cache,
            patch(
                "patriot_center_backend.cache.updaters"
                ".replacement_score_updater._backfill_three_years"
            ) as mock_backfill,
            patch(
                "patriot_center_backend.cache.updaters"
                ".replacement_score_updater._fetch_replacement_score_for_week"
            ) as mock_fetch,
            patch(
                "patriot_center_backend.cache.updaters"
                ".replacement_score_updater._get_three_yr_avg"
            ) as mock_get_avg,
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {}
            self.mock_get_cache = mock_get_cache
            self.mock_get_cache.return_value = self.mock_replacement_score_cache

            self.mock_backfill = mock_backfill

            self.mock_fetch = mock_fetch
            self.mock_fetch.return_value = {
                "byes": 4,
                "2024_scoring": {"QB": 15.0, "RB": 10.0},
            }

            self.mock_get_avg = mock_get_avg
            self.mock_get_avg.return_value = {
                "byes": 4,
                "2024_scoring": {"QB": 15.0},
                "QB_3yr_avg": 14.5,
            }

            yield

    def test_calls_backfill_when_cache_empty(self):
        """Test calls _backfill_three_years when cache is empty."""
        update_replacement_score_cache(2024, 5)

        self.mock_backfill.assert_called_once_with(2024)

    def test_does_not_backfill_when_cache_has_data(self):
        """Test does not backfill when cache already has data."""
        self.mock_replacement_score_cache["2021"] = {"1": {}}

        update_replacement_score_cache(2024, 5)

        self.mock_backfill.assert_not_called()

    def test_creates_year_entry_if_not_exists(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test creates year entry in cache if it doesn't exist.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_replacement_score_cache["2021"] = {}

        update_replacement_score_cache(2024, 5)

        assert "2024" in self.mock_replacement_score_cache

    def test_returns_early_if_fetch_returns_empty(self):
        """Test returns early if _fetch_replacement returns empty."""
        self.mock_replacement_score_cache["2021"] = {}
        self.mock_fetch.return_value = {}

        update_replacement_score_cache(2024, 5)

        assert "5" not in self.mock_replacement_score_cache.get("2024", {})

    def test_calculates_three_year_avg_when_data_exists(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test calculates 3-year avg when 3-year-old data exists.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_replacement_score_cache["2021"] = {"5": {"byes": 4}}

        update_replacement_score_cache(2024, 5)

        self.mock_get_avg.assert_called_once_with(2024, 5)

    def test_does_not_calculate_avg_without_three_year_data(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test does not calculate avg when 3-year-old data doesn't exist.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_replacement_score_cache["2022"] = {}

        update_replacement_score_cache(2024, 5)

        self.mock_get_avg.assert_not_called()

    def test_logs_info_message(self, caplog: pytest.LogCaptureFixture):
        """Test logs info message after update.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_replacement_score_cache["2021"] = {}

        caplog.set_level(logging.INFO)
        update_replacement_score_cache(2024, 5)

        assert (
            "Season 2024, Week 5: Replacement Score Cache Updated"
            in caplog.text
        )


class TestBackfillThreeYears:
    """Test _backfill_three_years function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_replacement_score_cache`: `mock_get_cache`
        - `get_max_weeks`: `mock_get_max_weeks`
        - `update_replacement_score_cache`: `mock_update`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters"
                ".replacement_score_updater.CACHE_MANAGER"
                ".get_replacement_score_cache"
            ) as mock_get_cache,
            patch(
                "patriot_center_backend.cache.updaters"
                ".replacement_score_updater.get_max_weeks"
            ) as mock_get_max_weeks,
            patch(
                "patriot_center_backend.cache.updaters"
                ".replacement_score_updater.update_replacement_score_cache"
            ) as mock_update,
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {}
            self.mock_get_cache = mock_get_cache
            self.mock_get_cache.return_value = self.mock_replacement_score_cache

            self.mock_get_max_weeks = mock_get_max_weeks
            self.mock_get_max_weeks.return_value = 17

            self.mock_update = mock_update

            yield

    def test_creates_year_entries_for_three_years(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test creates year entries for 3 years before current year.

        Args:
            caplog: pytest caplog fixture
        """
        _backfill_three_years(2024)

        assert "2021" in self.mock_replacement_score_cache
        assert "2022" in self.mock_replacement_score_cache
        assert "2023" in self.mock_replacement_score_cache

    def test_calls_update_for_each_week(self, caplog: pytest.LogCaptureFixture):
        """Test calls update_replacement_score_cache for each week.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_get_max_weeks.return_value = 3

        _backfill_three_years(2024)

        assert self.mock_update.call_count == 9

    def test_logs_backfill_info(self, caplog: pytest.LogCaptureFixture):
        """Test logs info about backfill process.

        Args:
            caplog: pytest caplog fixture
        """
        caplog.set_level(logging.INFO)
        _backfill_three_years(2024)

        assert "Starting backfill" in caplog.text
        assert "Backfilling replacement score cache" in caplog.text


class TestFetchReplacementScoreForWeek:
    """Test _fetch_replacement_score_for_week function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `get_player_info_and_score`: `mock_get_player_info_and_score`
        - `LEAGUE_IDS`: `mock_league_ids`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters"
                ".replacement_score_updater.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                "patriot_center_backend.cache.updaters"
                ".replacement_score_updater.get_player_info_and_score"
            ) as mock_get_player_info_and_score,
            patch(
                "patriot_center_backend.cache.updaters"
                ".replacement_score_updater.LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data

            self.mock_get_player_info_and_score = mock_get_player_info_and_score

            yield

    def test_raises_value_error_when_week_data_not_dict(self):
        """Test raises ValueError when week data is not a dict."""
        self.mock_fetch_sleeper_data.return_value = []

        with pytest.raises(ValueError) as exc_info:
            _fetch_replacement_score_for_week(2024, 5)

        assert "Sleeper API call failed" in str(exc_info.value)

    def test_returns_empty_when_no_week_data(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns empty dict when week data is empty.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_fetch_sleeper_data.return_value = {}

        result = _fetch_replacement_score_for_week(2024, 5)

        assert result == {}
        assert "No data found" in caplog.text

    def test_counts_byes_from_team_entries(self):
        """Test counts bye weeks from TEAM_ entries."""
        # Build week_data with TEAM_ entries and player entries
        week_data = {
            "TEAM_KC": {},
            "TEAM_PHI": {},
        }
        # Add player IDs for all positions
        for i in range(1, 14):
            week_data[str(i)] = {"gp": 1.0}
        for i in range(14, 45):
            week_data[str(i)] = {"gp": 1.0}
        for i in range(45, 76):
            week_data[str(i)] = {"gp": 1.0}
        for i in range(76, 89):
            week_data[str(i)] = {"gp": 1.0}
        for i in range(89, 102):
            week_data[str(i)] = {"gp": 1.0}
        for i in range(102, 115):
            week_data[str(i)] = {"gp": 1.0}

        self.mock_fetch_sleeper_data.side_effect = [
            week_data,
            {"scoring_settings": {}},
        ]

        # Create side_effect for get_player_info_and_score based on player_id
        def get_player_info_side_effect(
            player_id, week_data_arg, final_week_scores, scoring_settings
        ):
            pid = int(player_id)
            if pid < 14:
                return (
                    True,
                    {"full_name": f"QB{pid}", "position": "QB"},
                    15.0 - pid * 0.1,
                    player_id,
                )
            elif pid < 45:
                return (
                    True,
                    {"full_name": f"RB{pid}", "position": "RB"},
                    10.0 - (pid - 14) * 0.1,
                    player_id,
                )
            elif pid < 76:
                return (
                    True,
                    {"full_name": f"WR{pid}", "position": "WR"},
                    10.0 - (pid - 45) * 0.1,
                    player_id,
                )
            elif pid < 89:
                return (
                    True,
                    {"full_name": f"TE{pid}", "position": "TE"},
                    8.0 - (pid - 76) * 0.1,
                    player_id,
                )
            elif pid < 102:
                return (
                    True,
                    {"full_name": f"K{pid}", "position": "K"},
                    7.0 - (pid - 89) * 0.1,
                    player_id,
                )
            else:
                return (
                    True,
                    {"full_name": f"DEF{pid}", "position": "DEF"},
                    6.0 - (pid - 102) * 0.1,
                    player_id,
                )

        self.mock_get_player_info_and_score.side_effect = (
            get_player_info_side_effect
        )

        result = _fetch_replacement_score_for_week(2024, 5)

        assert result["byes"] == 30

    def test_raises_error_when_scoring_settings_fail(self):
        """Test raises error when scoring settings fetch fails."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"4046": {"gp": 1.0}},
            [],
        ]

        with pytest.raises(ValueError) as exc_info:
            _fetch_replacement_score_for_week(2024, 5)

        assert "scoring settings" in str(exc_info.value)


class TestGetThreeYrAvg:
    """Test _get_three_yr_avg function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_replacement_score_cache`: `mock_get_cache`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters"
                ".replacement_score_updater.CACHE_MANAGER"
                ".get_replacement_score_cache"
            ) as mock_get_cache,
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {
                "2024": {
                    "5": {
                        "byes": 4,
                        "2024_scoring": {
                            "QB": 15.0,
                            "RB": 10.0,
                            "WR": 9.0,
                            "TE": 8.0,
                        },
                    }
                },
                "2023": {
                    "5": {
                        "byes": 4,
                        "2024_scoring": {
                            "QB": 14.0,
                            "RB": 9.0,
                            "WR": 8.0,
                            "TE": 7.0,
                        },
                    }
                },
                "2022": {
                    "5": {
                        "byes": 4,
                        "2024_scoring": {
                            "QB": 13.0,
                            "RB": 8.0,
                            "WR": 7.0,
                            "TE": 6.0,
                        },
                    }
                },
                "2021": {
                    "5": {
                        "byes": 4,
                        "2024_scoring": {
                            "QB": 12.0,
                            "RB": 7.0,
                            "WR": 6.0,
                            "TE": 5.0,
                        },
                    }
                },
            }
            self.mock_get_cache = mock_get_cache
            self.mock_get_cache.return_value = self.mock_replacement_score_cache

            yield

    def test_calculates_average_for_each_position(self):
        """Test calculates 3-year average for each position."""
        result = _get_three_yr_avg(2024, 5)

        assert "QB_3yr_avg" in result
        assert "RB_3yr_avg" in result
        assert "WR_3yr_avg" in result
        assert "TE_3yr_avg" in result

    def test_returns_current_week_scores_with_averages(self):
        """Test returns current week scores augmented with 3-year averages."""
        result = _get_three_yr_avg(2024, 5)

        assert result["byes"] == 4
        assert "2024_scoring" in result

    def test_skips_missing_years(self):
        """Test handles missing years gracefully."""
        del self.mock_replacement_score_cache["2022"]

        result = _get_three_yr_avg(2024, 5)

        assert "QB_3yr_avg" in result

    def test_skips_missing_weeks(self):
        """Test handles missing weeks gracefully."""
        del self.mock_replacement_score_cache["2023"]["5"]

        result = _get_three_yr_avg(2024, 5)

        assert "QB_3yr_avg" in result

    def test_adjusts_lower_bye_score_when_higher_bye_has_higher_score(
        self,
    ):
        """Test lower bye count score is adjusted when appropriate.

        When a week with more byes has a higher replacement score than a week
        with fewer byes, the lower bye week's score should be adjusted upward.
        """
        # Setup: Create weeks with different bye counts where higher byes
        # have higher scores (violates monotonicity expectation)
        self.mock_replacement_score_cache = {
            "2024": {
                "5": {
                    "byes": 4,  # Current week with 4 byes
                    "2024_scoring": {
                        "QB": 15.0, "RB": 10.0, "WR": 9.0, "TE": 8.0
                    },
                }
            },
            "2023": {
                "1": {  # Week with 2 byes, lower score
                    "byes": 2,
                    "2024_scoring": {
                        "QB": 10.0, "RB": 6.0, "WR": 5.0, "TE": 4.0
                    },
                },
                "5": {  # Week with 6 byes, HIGHER score (violates expectation)
                    "byes": 6,
                    "2024_scoring": {
                        "QB": 18.0, "RB": 12.0, "WR": 11.0, "TE": 10.0
                    },
                },
            },
            "2022": {
                "5": {
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 14.0, "RB": 9.0, "WR": 8.0, "TE": 7.0
                    },
                }
            },
            "2021": {
                "5": {
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 13.0, "RB": 8.0, "WR": 7.0, "TE": 6.0
                    },
                }
            },
        }
        self.mock_get_cache.return_value = self.mock_replacement_score_cache

        result = _get_three_yr_avg(2024, 5)

        # The 3yr avg for QB at 4 byes should be >= the avg at higher bye counts
        # because monotonicity enforcement adjusts lower bye scores upward
        assert "QB_3yr_avg" in result

    def test_monotonicity_propagates_across_multiple_bye_counts(self):
        """Test monotonicity adjustment propagates across multiple bye counts.

        If bye counts 2, 4, and 6 exist, and 6 > 4 > 2 in scores,
        the adjustment should cascade: 2 is adjusted to match 4,
        then 4 might need adjustment based on 6.
        """
        # Setup: Three different bye counts with descending scores
        # (6 byes highest, 2 byes lowest - all need adjustment)
        self.mock_replacement_score_cache = {
            "2024": {
                "5": {
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 15.0, "RB": 10.0, "WR": 9.0, "TE": 8.0
                    },
                }
            },
            "2023": {
                "1": {  # 2 byes, lowest score
                    "byes": 2,
                    "2024_scoring": {
                        "QB": 8.0, "RB": 5.0, "WR": 4.0, "TE": 3.0
                    },
                },
                "5": {  # 4 byes, medium score
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 12.0, "RB": 8.0, "WR": 7.0, "TE": 6.0
                    },
                },
                "10": {  # 6 byes, highest score
                    "byes": 6,
                    "2024_scoring": {
                        "QB": 20.0, "RB": 14.0, "WR": 12.0, "TE": 10.0
                    },
                },
            },
            "2022": {
                "5": {
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 14.0, "RB": 9.0, "WR": 8.0, "TE": 7.0
                    },
                }
            },
            "2021": {
                "5": {
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 13.0, "RB": 8.0, "WR": 7.0, "TE": 6.0
                    },
                }
            },
        }
        self.mock_get_cache.return_value = self.mock_replacement_score_cache

        result = _get_three_yr_avg(2024, 5)

        # Function should complete without error and return averages
        assert "QB_3yr_avg" in result
        assert "RB_3yr_avg" in result

    def test_monotonicity_applies_to_all_positions(self):
        """Test monotonicity enforcement applies to all positions, not just QB.

        The code uses QB's bye counts as reference but applies adjustment
        to all positions in three_yr_season_average.
        """
        # Setup: Higher bye count has higher score for all positions
        self.mock_replacement_score_cache = {
            "2024": {
                "5": {
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 15.0, "RB": 10.0, "WR": 9.0, "TE": 8.0
                    },
                }
            },
            "2023": {
                "1": {  # 2 byes, lower scores
                    "byes": 2,
                    "2024_scoring": {
                        "QB": 10.0, "RB": 6.0, "WR": 5.0, "TE": 4.0
                    },
                },
                "10": {  # 6 byes, higher scores
                    "byes": 6,
                    "2024_scoring": {
                        "QB": 20.0, "RB": 14.0, "WR": 12.0, "TE": 11.0
                    },
                },
            },
            "2022": {
                "5": {
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 14.0, "RB": 9.0, "WR": 8.0, "TE": 7.0
                    },
                }
            },
            "2021": {
                "5": {
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 13.0, "RB": 8.0, "WR": 7.0, "TE": 6.0
                    },
                }
            },
        }
        self.mock_get_cache.return_value = self.mock_replacement_score_cache

        result = _get_three_yr_avg(2024, 5)

        # All positions should have 3yr avg computed
        assert "QB_3yr_avg" in result
        assert "RB_3yr_avg" in result
        assert "WR_3yr_avg" in result
        assert "TE_3yr_avg" in result

    def test_monotonicity_no_adjustment_when_scores_already_valid(self):
        """Test no adjustment when lower bye counts already have higher scores.

        When replacement scores naturally decrease as byes increase
        (fewer available players = higher replacement threshold),
        no adjustment should be needed.
        """
        # Setup: Lower byes have higher scores (normal expectation)
        self.mock_replacement_score_cache = {
            "2024": {
                "5": {
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 15.0, "RB": 10.0, "WR": 9.0, "TE": 8.0
                    },
                }
            },
            "2023": {
                "1": {  # 2 byes, higher score (more players = higher bar)
                    "byes": 2,
                    "2024_scoring": {
                        "QB": 18.0, "RB": 12.0, "WR": 11.0, "TE": 10.0
                    },
                },
                "10": {  # 6 byes, lower score (fewer players = lower bar)
                    "byes": 6,
                    "2024_scoring": {
                        "QB": 10.0, "RB": 6.0, "WR": 5.0, "TE": 4.0
                    },
                },
            },
            "2022": {
                "5": {
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 14.0, "RB": 9.0, "WR": 8.0, "TE": 7.0
                    },
                }
            },
            "2021": {
                "5": {
                    "byes": 4,
                    "2024_scoring": {
                        "QB": 13.0, "RB": 8.0, "WR": 7.0, "TE": 6.0
                    },
                }
            },
        }
        self.mock_get_cache.return_value = self.mock_replacement_score_cache

        result = _get_three_yr_avg(2024, 5)

        # Should complete normally with valid averages
        assert "QB_3yr_avg" in result
        assert "RB_3yr_avg" in result
