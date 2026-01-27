"""Unit tests for _base module."""

from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.cache.updaters._base import (
    get_max_weeks,
    get_player_info_and_score,
)


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


class TestGetPlayerInfoAndScore:
    """Test get_player_info_and_score function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`: `mock_get_player_ids_cache`
        - `calculate_player_score`: `mock_calculate_player_score`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.cache.updaters._base"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids_cache,
            patch(
                "patriot_center_backend.cache.updaters._base"
                ".calculate_player_score"
            ) as mock_calculate_player_score,
        ):
            self.mock_player_ids_cache: dict[str, Any] = {
                "4046": {
                    "full_name": "Patrick Mahomes",
                    "position": "QB",
                },
                "6744": {
                    "full_name": "Josh Allen",
                    "position": "QB",
                },
                "1234": {
                    "full_name": "Zach Ertz",
                    "position": "TE",
                },
                "KC": {
                    "full_name": "Kansas City Chiefs",
                    "position": "DEF",
                },
            }
            self.mock_get_player_ids_cache = mock_get_player_ids_cache
            self.mock_get_player_ids_cache.return_value = (
                self.mock_player_ids_cache
            )

            self.mock_calculate_player_score = mock_calculate_player_score
            self.mock_calculate_player_score.return_value = 25.0

            yield

    def test_returns_false_when_player_not_in_cache(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns False when player_id is not in cache.

        Args:
            caplog: pytest caplog fixture
        """
        week_data = {"9999": {"gp": 1.0, "pass_yd": 300}}
        final_week_scores = {
            "QB": {},
            "RB": {},
            "WR": {},
            "TE": {},
            "K": {},
            "DEF": {},
        }
        scoring_settings = {"pass_yd": 0.04}

        apply, player_info, score, player_id = get_player_info_and_score(
            "9999", week_data, final_week_scores, scoring_settings
        )

        assert apply is False
        assert player_info == {}
        assert score == 0.0
        assert player_id == "9999"

    def test_returns_false_when_player_has_zero_games_played(self):
        """Test returns False when player has gp = 0."""
        week_data = {"4046": {"gp": 0.0, "pass_yd": 300}}
        final_week_scores = {
            "QB": {},
            "RB": {},
            "WR": {},
            "TE": {},
            "K": {},
            "DEF": {},
        }
        scoring_settings = {"pass_yd": 0.04}

        apply, _, score, _ = get_player_info_and_score(
            "4046", week_data, final_week_scores, scoring_settings
        )

        assert apply is False
        assert score == 0.0

    def test_returns_false_for_numeric_def_player_id(self):
        """Test returns False when position is DEF and ID is numeric."""
        self.mock_player_ids_cache["1111"] = {
            "full_name": "Some Defense",
            "position": "DEF",
        }
        week_data = {"1111": {"gp": 1.0}}
        final_week_scores = {
            "QB": {},
            "RB": {},
            "WR": {},
            "TE": {},
            "K": {},
            "DEF": {},
        }
        scoring_settings = {}

        apply, _, score, _ = get_player_info_and_score(
            "1111", week_data, final_week_scores, scoring_settings
        )

        assert apply is False
        assert score == 0.0

    def test_returns_true_for_valid_player(self):
        """Test returns True with correct info for valid player."""
        week_data = {"4046": {"gp": 1.0, "pass_yd": 300}}
        final_week_scores = {
            "QB": {},
            "RB": {},
            "WR": {},
            "TE": {},
            "K": {},
            "DEF": {},
        }
        scoring_settings = {"pass_yd": 0.04}

        apply, player_info, score, player_id = get_player_info_and_score(
            "4046", week_data, final_week_scores, scoring_settings
        )

        assert apply is True
        assert player_info["full_name"] == "Patrick Mahomes"
        assert player_info["position"] == "QB"
        assert score == 25.0
        assert player_id == "4046"

    def test_handles_player_id_with_non_numeric_suffix(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test handles player IDs with non-numeric chars (Zach Ertz case).

        Args:
            caplog: pytest caplog fixture
        """
        week_data = {"1234ARI": {"gp": 1.0, "rec_yd": 50}}
        final_week_scores = {
            "QB": {},
            "RB": {},
            "WR": {},
            "TE": {},
            "K": {},
            "DEF": {},
        }
        scoring_settings = {"rec_yd": 0.1}

        apply, player_info, _, player_id = get_player_info_and_score(
            "1234ARI", week_data, final_week_scores, scoring_settings
        )

        assert apply is True
        assert player_info["full_name"] == "Zach Ertz"
        assert player_id == "1234"

    def test_skips_duplicate_when_numeric_id_exists_in_week_data(self):
        """Test skips player when numeric ID also exists in week_data."""
        week_data = {
            "1234ARI": {"gp": 1.0, "rec_yd": 50},
            "1234": {"gp": 1.0, "rec_yd": 60},
        }
        final_week_scores = {
            "QB": {},
            "RB": {},
            "WR": {},
            "TE": {},
            "K": {},
            "DEF": {},
        }
        scoring_settings = {"rec_yd": 0.1}

        apply, _, _, player_id = get_player_info_and_score(
            "1234ARI", week_data, final_week_scores, scoring_settings
        )

        assert apply is False
        assert player_id == "1234ARI"

    def test_returns_false_for_position_not_in_final_week_scores(self):
        """Test returns False when player position not in final_week_scores."""
        self.mock_player_ids_cache["9999"] = {
            "full_name": "Some Player",
            "position": "LB",
        }
        week_data = {"9999": {"gp": 1.0}}
        final_week_scores = {
            "QB": {},
            "RB": {},
            "WR": {},
            "TE": {},
            "K": {},
            "DEF": {},
        }
        scoring_settings = {}

        apply, _, _, _ = get_player_info_and_score(
            "9999", week_data, final_week_scores, scoring_settings
        )

        assert apply is False

    def test_returns_true_for_non_numeric_def_id(self):
        """Test returns True for DEF with non-numeric ID (like 'KC')."""
        week_data = {"KC": {"gp": 1.0, "pts_allow": 14}}
        final_week_scores = {
            "QB": {},
            "RB": {},
            "WR": {},
            "TE": {},
            "K": {},
            "DEF": {},
        }
        scoring_settings = {"pts_allow_0_6": 7.0}

        apply, player_info, _, _ = get_player_info_and_score(
            "KC", week_data, final_week_scores, scoring_settings
        )

        assert apply is True
        assert player_info["full_name"] == "Kansas City Chiefs"
        assert player_info["position"] == "DEF"
