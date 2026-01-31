"""Unit tests for replacement_score_updater module."""

import logging
from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters.replacement_score_updater import (
    ReplacementScoreCacheBuilder,
)

MODULE_PATH = "patriot_center_backend.cache.updaters.replacement_score_updater"


class TestReplacementScoreCacheBuilderInit:
    """Test ReplacementScoreCacheBuilder.__init__ method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_replacement_score_cache`:
            `mock_get_replacement_score_cache`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `ReplacementScoreCacheBuilder._initial_three_year_backfill`:
            mocked to no-op
        - `LEAGUE_IDS`: mock league IDs

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score_cache,
            patch(
                f"{MODULE_PATH}.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch.object(
                ReplacementScoreCacheBuilder,
                "_initial_three_year_backfill",
            ),
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024", 2025: "league2025"},
            ),
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {}
            mock_get_replacement_score_cache.return_value = (
                self.mock_replacement_score_cache
            )

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.side_effect = [
                {"4046": {"gp": 1.0}},
                {"scoring_settings": {"pass_yd": 0.04}},
                {"scoring_settings": {"pass_yd": 0.04}},
            ]

            yield

    def test_sets_week_to_1_for_empty_cache(self):
        """Test starts at week 1 when cache is empty."""
        builder = ReplacementScoreCacheBuilder(2024)

        assert builder.week == 1

    def test_sets_week_after_last_cached(self):
        """Test starts at last cached week + 1."""
        self.mock_replacement_score_cache["2024"] = {"5": {}}

        builder = ReplacementScoreCacheBuilder(2024)

        assert builder.week == 6


class TestUpdate:
    """Test ReplacementScoreCacheBuilder.update method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_replacement_score_cache`:
            `mock_get_replacement_score_cache`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `log_cache_update`: `mock_log_cache_update`
        - `calculate_three_year_averages`:
            `mock_calculate_three_year_averages`
        - `get_player_info_and_score`:
            `mock_get_player_info_and_score`
        - `ReplacementScoreCacheBuilder._initial_three_year_backfill`:
            mocked to no-op
        - `LEAGUE_IDS`: mock league IDs

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score_cache,
            patch(
                f"{MODULE_PATH}.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(f"{MODULE_PATH}.log_cache_update") as mock_log_cache_update,
            patch(
                f"{MODULE_PATH}.calculate_three_year_averages"
            ) as mock_calculate_three_year_averages,
            patch(
                f"{MODULE_PATH}.get_player_info_and_score"
            ) as mock_get_player_info_and_score,
            patch.object(
                ReplacementScoreCacheBuilder,
                "_initial_three_year_backfill",
            ),
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {}
            mock_get_replacement_score_cache.return_value = (
                self.mock_replacement_score_cache
            )

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.side_effect = [
                {"4046": {"gp": 1.0}},
                {"scoring_settings": {"pass_yd": 0.04}},
                "not_a_dict",
            ]

            self.mock_log_cache_update = mock_log_cache_update
            self.mock_calculate_three_year_averages = (
                mock_calculate_three_year_averages
            )

            self.mock_get_player_info_and_score = mock_get_player_info_and_score
            self.mock_get_player_info_and_score.return_value = (
                False,
                {},
                0.0,
                "4046",
            )

            yield

    def test_returns_when_no_week_data(self):
        """Test returns early when no week data."""
        builder = ReplacementScoreCacheBuilder(2024)
        # Manually clear week_data to simulate no data available
        builder.week_data = {}

        builder.update()

        self.mock_log_cache_update.assert_not_called()

    def test_logs_cache_update(self):
        """Test logs cache update for each week processed."""
        builder = ReplacementScoreCacheBuilder(2024)

        def stop_after_first_week():
            builder.week += 1
            builder.week_data = {}

        with (
            patch.object(
                builder,
                "_fetch_replacement_score_for_week",
                return_value={"byes": 30, "2024_scoring": {"QB": 15.0}},
            ),
            patch.object(
                builder,
                "_proceed_to_next_week",
                side_effect=stop_after_first_week,
            ),
        ):
            builder.update()

        self.mock_log_cache_update.assert_called()

    def test_stores_result_in_cache(self):
        """Test stores replacement score result in cache."""
        builder = ReplacementScoreCacheBuilder(2024)

        def stop_after_first_week():
            builder.week += 1
            builder.week_data = {}

        with (
            patch.object(
                builder,
                "_fetch_replacement_score_for_week",
                return_value={"byes": 30, "2024_scoring": {"QB": 15.0}},
            ),
            patch.object(
                builder,
                "_proceed_to_next_week",
                side_effect=stop_after_first_week,
            ),
        ):
            builder.update()

        assert "2024" in self.mock_replacement_score_cache
        assert "1" in self.mock_replacement_score_cache["2024"]


class TestGetNextWeekToUpdate:
    """Test ReplacementScoreCacheBuilder._get_next_week_to_update method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score_cache,
            patch(
                f"{MODULE_PATH}.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch.object(
                ReplacementScoreCacheBuilder,
                "_initial_three_year_backfill",
            ),
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {}
            mock_get_replacement_score_cache.return_value = (
                self.mock_replacement_score_cache
            )

            mock_fetch_sleeper_data.side_effect = [
                {"4046": {"gp": 1.0}},
                {"scoring_settings": {"pass_yd": 0.04}},
            ]

            yield

    def test_returns_1_for_empty_cache(self):
        """Test returns 1 when no data in cache for year."""
        builder = ReplacementScoreCacheBuilder(2024)

        assert builder.week == 1

    def test_returns_last_week_plus_1(self):
        """Test returns last cached week + 1."""
        self.mock_replacement_score_cache["2024"] = {
            "1": {},
            "2": {},
            "3": {},
        }

        builder = ReplacementScoreCacheBuilder(2024)

        assert builder.week == 4


class TestHasThreeYearAverages:
    """Test ReplacementScoreCacheBuilder._has_three_year_averages method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score_cache,
            patch(
                f"{MODULE_PATH}.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch.object(
                ReplacementScoreCacheBuilder,
                "_initial_three_year_backfill",
            ),
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {}
            mock_get_replacement_score_cache.return_value = (
                self.mock_replacement_score_cache
            )

            mock_fetch_sleeper_data.side_effect = [
                {"4046": {"gp": 1.0}},
                {"scoring_settings": {"pass_yd": 0.04}},
            ]

            yield

    def test_returns_true_when_three_years_ago_exists(self):
        """Test returns True when 3 years ago data exists."""
        self.mock_replacement_score_cache["2021"] = {"1": {}}

        builder = ReplacementScoreCacheBuilder(2024)

        assert builder._has_three_year_averages() is True

    def test_returns_false_when_three_years_ago_missing(self):
        """Test returns False when 3 years ago data is missing."""
        builder = ReplacementScoreCacheBuilder(2024)

        assert builder._has_three_year_averages() is False


class TestSetWeekData:
    """Test ReplacementScoreCacheBuilder._set_week_data method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score_cache,
            patch(
                f"{MODULE_PATH}.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch.object(
                ReplacementScoreCacheBuilder,
                "_initial_three_year_backfill",
            ),
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {}
            mock_get_replacement_score_cache.return_value = (
                self.mock_replacement_score_cache
            )

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.side_effect = [
                {"4046": {"gp": 1.0}},
                {"scoring_settings": {"pass_yd": 0.04}},
            ]

            yield

    def test_sets_week_data_from_api(self):
        """Test sets week_data from Sleeper API response."""
        builder = ReplacementScoreCacheBuilder(2024)

        assert builder.week_data == {"4046": {"gp": 1.0}}

    def test_raises_when_api_returns_non_dict(self):
        """Test raises ValueError when API returns non-dict."""
        self.mock_fetch_sleeper_data.side_effect = [
            "not_a_dict",
            {"scoring_settings": {}},
        ]

        with pytest.raises(ValueError) as exc_info:
            ReplacementScoreCacheBuilder(2024)

        assert "Sleeper API call failed" in str(exc_info.value)


class TestSetYearlyScoringSettings:
    """Test ReplacementScoreCacheBuilder._set_yearly_score_settings method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score_cache,
            patch(
                f"{MODULE_PATH}.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch.object(
                ReplacementScoreCacheBuilder,
                "_initial_three_year_backfill",
            ),
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024", 2025: "league2025"},
            ),
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {}
            mock_get_replacement_score_cache.return_value = (
                self.mock_replacement_score_cache
            )

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.side_effect = [
                {"4046": {"gp": 1.0}},
                {"scoring_settings": {"pass_yd": 0.04}},
                {"scoring_settings": {"pass_yd": 0.05}},
            ]

            yield

    def test_loads_scoring_settings_for_valid_years(self):
        """Test loads scoring settings for years in LEAGUE_IDS."""
        builder = ReplacementScoreCacheBuilder(2024)

        assert 2024 in builder.yearly_score_settings
        assert 2025 in builder.yearly_score_settings

    def test_raises_when_api_returns_non_dict(self):
        """Test raises ValueError when API returns non-dict."""
        self.mock_fetch_sleeper_data.side_effect = [
            {"4046": {"gp": 1.0}},
            "not_a_dict",
        ]

        with pytest.raises(ValueError) as exc_info:
            ReplacementScoreCacheBuilder(2024)

        assert "Sleeper API call failed" in str(exc_info.value)


class TestProceedToNextWeek:
    """Test ReplacementScoreCacheBuilder._proceed_to_next_week method."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_replacement_score_cache`:
            `mock_get_replacement_score_cache`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `ReplacementScoreCacheBuilder._initial_three_year_backfill`:
            mocked to no-op
        - `LEAGUE_IDS`: mock league IDs

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score_cache,
            patch(
                f"{MODULE_PATH}.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch.object(
                ReplacementScoreCacheBuilder,
                "_initial_three_year_backfill",
            ),
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {}
            mock_get_replacement_score_cache.return_value = (
                self.mock_replacement_score_cache
            )

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data
            self.mock_fetch_sleeper_data.side_effect = [
                # __init__: _set_week_data
                {"4046": {"gp": 1.0}},
                # __init__: _set_yearly_score_settings
                {"scoring_settings": {"pass_yd": 0.04}},
                # _proceed_to_next_week: _set_week_data
                {"6794": {"gp": 1.0}},
            ]

            yield

    def test_increments_week(self):
        """Test increments week by 1."""
        builder = ReplacementScoreCacheBuilder(2024)

        assert builder.week == 1

        builder._proceed_to_next_week()

        assert builder.week == 2

    def test_fetches_new_week_data(self):
        """Test fetches new week data after incrementing."""
        builder = ReplacementScoreCacheBuilder(2024)

        builder._proceed_to_next_week()

        assert builder.week_data == {"6794": {"gp": 1.0}}


class TestFetchReplacementScoreForWeek:
    """Test ReplacementScoreCacheBuilder._fetch_replacement_score_for_week."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_replacement_score_cache`:
            `mock_get_replacement_score_cache`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `get_player_info_and_score`:
            `mock_get_player_info_and_score`
        - `ReplacementScoreCacheBuilder._initial_three_year_backfill`:
            mocked to no-op
        - `LEAGUE_IDS`: mock league IDs

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score_cache,
            patch(
                f"{MODULE_PATH}.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                f"{MODULE_PATH}.get_player_info_and_score"
            ) as mock_get_player_info_and_score,
            patch.object(
                ReplacementScoreCacheBuilder,
                "_initial_three_year_backfill",
            ),
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {}
            mock_get_replacement_score_cache.return_value = (
                self.mock_replacement_score_cache
            )

            # Build week_data with TEAM entries + enough players
            week_data: dict[str, Any] = {}
            # Add 2 TEAM entries (byes = 32 - 2 = 30)
            week_data["TEAM_KC"] = {"pts": 30}
            week_data["TEAM_SF"] = {"pts": 25}

            # Need 13+ QB, 31+ RB, 31+ WR, 13+ TE, 13+ K, 13+ DEF
            positions_needed = (
                [("QB", 15), ("RB", 35), ("WR", 35), ("TE", 15), ("K", 15), ("DEF", 15)]  # noqa: E501
            )
            pid = 1000
            self._position_map: dict[str, str] = {}
            for pos, count in positions_needed:
                for _ in range(count):
                    pid += 1
                    week_data[str(pid)] = {"gp": 1.0}
                    self._position_map[str(pid)] = pos

            mock_fetch_sleeper_data.side_effect = [
                week_data,
                {"scoring_settings": {"pass_yd": 0.04}},
            ]

            self.mock_get_player_info_and_score = (
                mock_get_player_info_and_score
            )

            score_counter = iter(range(50, -100, -1))

            def side_effect(pid, wd, ws, ss):
                pos = self._position_map.get(pid, "QB")
                score = float(next(score_counter))
                return (True, {"position": pos}, score, pid)

            self.mock_get_player_info_and_score.side_effect = side_effect

            yield

    def test_returns_dict_with_byes(self):
        """Test result contains byes count."""
        builder = ReplacementScoreCacheBuilder(2024)

        result = builder._fetch_replacement_score_for_week()

        assert "byes" in result
        assert result["byes"] == 30

    def test_returns_dict_with_scoring_key(self):
        """Test result contains year scoring key."""
        builder = ReplacementScoreCacheBuilder(2024)

        result = builder._fetch_replacement_score_for_week()

        assert "2024_scoring" in result

    def test_decrements_byes_for_team_entries(self):
        """Test TEAM_ entries decrement byes from 32."""
        builder = ReplacementScoreCacheBuilder(2024)

        result = builder._fetch_replacement_score_for_week()

        # 32 - 2 TEAM entries = 30
        assert result["byes"] == 30

    def test_skips_team_entries_for_scoring(self):
        """Test TEAM_ entries are not passed to get_player_info_and_score."""
        builder = ReplacementScoreCacheBuilder(2024)

        builder._fetch_replacement_score_for_week()

        # 130 player entries, 2 TEAM entries skipped
        assert self.mock_get_player_info_and_score.call_count == 130


class TestUpdateWithThreeYearAverages:
    """Test update method when _has_three_year_averages returns True."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_replacement_score_cache`:
            `mock_get_replacement_score_cache`
        - `fetch_sleeper_data`: `mock_fetch_sleeper_data`
        - `log_cache_update`: (no-op)
        - `calculate_three_year_averages`:
            `mock_calculate_three_year_averages`
        - `ReplacementScoreCacheBuilder._initial_three_year_backfill`:
            mocked to no-op
        - `LEAGUE_IDS`: mock league IDs

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score_cache,
            patch(
                f"{MODULE_PATH}.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(f"{MODULE_PATH}.log_cache_update"),
            patch(
                f"{MODULE_PATH}.calculate_three_year_averages"
            ) as mock_calculate_three_year_averages,
            patch.object(
                ReplacementScoreCacheBuilder,
                "_initial_three_year_backfill",
            ),
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {
                "2021": {"1": {}},
            }
            mock_get_replacement_score_cache.return_value = (
                self.mock_replacement_score_cache
            )

            mock_fetch_sleeper_data.side_effect = [
                {"4046": {"gp": 1.0}},
                {"scoring_settings": {"pass_yd": 0.04}},
                "not_a_dict",
            ]

            self.mock_calculate_three_year_averages = (
                mock_calculate_three_year_averages
            )
            self.mock_calculate_three_year_averages.return_value = {
                "byes": 30,
                "QB_3yr_avg": 14.0,
            }

            yield

    def test_calls_calculate_three_year_averages(self):
        """Test calls calculate_three_year_averages when data exists."""
        builder = ReplacementScoreCacheBuilder(2024)

        def stop_after_first_week():
            builder.week += 1
            builder.week_data = {}

        with (
            patch.object(
                builder,
                "_fetch_replacement_score_for_week",
                return_value={"byes": 30, "2024_scoring": {"QB": 15.0}},
            ),
            patch.object(
                builder,
                "_proceed_to_next_week",
                side_effect=stop_after_first_week,
            ),
        ):
            builder.update()

        self.mock_calculate_three_year_averages.assert_called_once_with(
            2024, 1
        )

    def test_stores_three_year_avg_result_in_cache(self):
        """Test stores three year average result in cache."""
        builder = ReplacementScoreCacheBuilder(2024)

        def stop_after_first_week():
            builder.week += 1
            builder.week_data = {}

        with (
            patch.object(
                builder,
                "_fetch_replacement_score_for_week",
                return_value={"byes": 30, "2024_scoring": {"QB": 15.0}},
            ),
            patch.object(
                builder,
                "_proceed_to_next_week",
                side_effect=stop_after_first_week,
            ),
        ):
            builder.update()

        cached = self.mock_replacement_score_cache["2024"]["1"]
        assert cached["QB_3yr_avg"] == 14.0


class TestInitialThreeYearBackfill:
    """Test ReplacementScoreCacheBuilder._initial_three_year_backfill."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        Yields:
            None
        """
        with (
            patch(
                f"{MODULE_PATH}.CACHE_MANAGER.get_replacement_score_cache"
            ) as mock_get_replacement_score_cache,
            patch(
                f"{MODULE_PATH}.fetch_sleeper_data"
            ) as mock_fetch_sleeper_data,
            patch(
                f"{MODULE_PATH}.LEAGUE_IDS",
                {2024: "league2024"},
            ),
        ):
            self.mock_replacement_score_cache: dict[str, Any] = {}
            mock_get_replacement_score_cache.return_value = (
                self.mock_replacement_score_cache
            )

            self.mock_fetch_sleeper_data = mock_fetch_sleeper_data

            yield

    def test_skips_backfill_when_cache_not_empty(self):
        """Test skips backfill when replacement score cache is not empty."""
        self.mock_replacement_score_cache["2023"] = {"1": {}}

        self.mock_fetch_sleeper_data.side_effect = [
            {"4046": {"gp": 1.0}},
            {"scoring_settings": {"pass_yd": 0.04}},
        ]

        ReplacementScoreCacheBuilder(2024)

        # Only 2 calls: week data + scoring settings for init
        # No backfill calls
        assert self.mock_fetch_sleeper_data.call_count == 2

    def test_backfills_three_years_when_cache_empty(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test backfills 3 prior years when cache is empty.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_fetch_sleeper_data.side_effect = [
            # For each backfill year: week data returns empty
            # (no data triggers early return in update())
            # Year 2021
            {},
            {"scoring_settings": {"pass_yd": 0.04}},
            # Year 2022
            {},
            {"scoring_settings": {"pass_yd": 0.04}},
            # Year 2023
            {},
            {"scoring_settings": {"pass_yd": 0.04}},
            # Main builder (year 2024)
            {"4046": {"gp": 1.0}},
            {"scoring_settings": {"pass_yd": 0.04}},
        ]

        with caplog.at_level(logging.INFO):
            ReplacementScoreCacheBuilder(2024)

        assert "Starting backfill" in caplog.text
        # Backfill creates keys for years 2021, 2022, 2023
        assert "2021" in self.mock_replacement_score_cache
        assert "2022" in self.mock_replacement_score_cache
        assert "2023" in self.mock_replacement_score_cache
