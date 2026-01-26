"""Unit tests for _base module."""

from patriot_center_backend.cache.updaters._base import get_max_weeks


class TestGetMaxWeeks:
    """Test get_max_weeks function."""

    def test_returns_current_week_for_current_season(self):
        """Test returns current_week when season matches current_season."""
        result = get_max_weeks(
            season=2024,
            current_season=2024,
            current_week=10,
        )

        assert result == 10

    def test_returns_current_week_for_current_season_with_true_max(self):
        """Test returns current_week even when true_max is True."""
        result = get_max_weeks(
            season=2024,
            current_season=2024,
            current_week=10,
            true_max=True,
        )

        assert result == 10

    def test_returns_16_for_2020_season_without_true_max(self):
        """Test returns 16 (cap - 1) for 2020 season."""
        result = get_max_weeks(
            season=2020,
            current_season=2024,
            current_week=10,
        )

        assert result == 16

    def test_returns_17_for_2020_season_with_true_max(self):
        """Test returns 17 (cap) for 2020 season when true_max is True."""
        result = get_max_weeks(
            season=2020,
            current_season=2024,
            current_week=10,
            true_max=True,
        )

        assert result == 17

    def test_returns_17_for_2021_and_later_without_true_max(self):
        """Test returns 17 (cap - 1) for 2021+ seasons."""
        result = get_max_weeks(
            season=2021,
            current_season=2024,
            current_week=10,
        )

        assert result == 17

    def test_returns_18_for_2021_and_later_with_true_max(self):
        """Test returns 18 (cap) for 2021+ seasons when true_max is True."""
        result = get_max_weeks(
            season=2021,
            current_season=2024,
            current_week=10,
            true_max=True,
        )

        assert result == 18

    def test_returns_16_for_pre_2020_season_without_true_max(self):
        """Test returns 16 (cap - 1) for pre-2020 seasons (e.g., 2019)."""
        result = get_max_weeks(
            season=2019,
            current_season=2024,
            current_week=10,
        )

        assert result == 16

    def test_returns_17_for_pre_2020_season_with_true_max(self):
        """Test returns 17 (cap) for pre-2020 seasons when true_max is True."""
        result = get_max_weeks(
            season=2019,
            current_season=2024,
            current_week=10,
            true_max=True,
        )

        assert result == 17

    def test_returns_cap_minus_one_when_current_week_is_none(self):
        """Test returns cap - 1 when current_week is None."""
        result = get_max_weeks(
            season=2023,
            current_season=2024,
            current_week=None,
        )

        assert result == 17

    def test_returns_cap_when_current_week_is_none_and_true_max(self):
        """Test returns cap when current_week is None and true_max is True."""
        result = get_max_weeks(
            season=2023,
            current_season=2024,
            current_week=None,
            true_max=True,
        )

        assert result == 18

    def test_returns_cap_minus_one_when_current_season_is_none(self):
        """Test returns cap - 1 when current_season is None."""
        result = get_max_weeks(
            season=2023,
            current_season=None,
            current_week=10,
        )

        assert result == 17

    def test_returns_cap_when_all_optional_params_are_none(self):
        """Test returns cap - 1 when all optional params are None."""
        result = get_max_weeks(season=2023)

        assert result == 17

    def test_returns_true_max_when_all_optional_params_are_none(self):
        """Test returns cap when all optional params are None and true_max."""
        result = get_max_weeks(season=2023, true_max=True)

        assert result == 18

    def test_boundary_year_2020_returns_correct_cap(self):
        """Test boundary year 2020 uses legacy cap of 17."""
        result = get_max_weeks(season=2020, true_max=True)

        assert result == 17

    def test_boundary_year_2021_returns_correct_cap(self):
        """Test boundary year 2021 uses modern cap of 18."""
        result = get_max_weeks(season=2021, true_max=True)

        assert result == 18
