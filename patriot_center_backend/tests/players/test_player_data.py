"""Unit tests for player_data module."""

import logging
from typing import Any
from unittest.mock import patch

import pytest

from patriot_center_backend.players.player_data import (
    get_player_info_and_score,
)


class TestGetPlayerInfoAndScore:
    """Test get_player_info_and_score function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup common mocks for all tests.

        The mocks are set up to return a pre-defined
        set of values when accessed.
        - `CACHE_MANAGER.get_player_ids_cache`:
            `mock_get_player_ids_cache`
        - `calculate_player_score`: `mock_calculate_player_score`

        Yields:
            None
        """
        with (
            patch(
                "patriot_center_backend.players.player_data"
                ".CACHE_MANAGER.get_player_ids_cache"
            ) as mock_get_player_ids_cache,
            patch(
                "patriot_center_backend.players.player_data"
                ".calculate_player_score"
            ) as mock_calculate_player_score,
        ):
            self.mock_player_ids_cache: dict[str, dict[str, Any]] = {
                "4046": {
                    "full_name": "Patrick Mahomes",
                    "position": "QB",
                },
                "SEA": {
                    "full_name": "Seattle Seahawks",
                    "position": "DEF",
                },
                "6794": {
                    "full_name": "Jayden Daniels",
                    "position": "QB",
                },
            }
            mock_get_player_ids_cache.return_value = self.mock_player_ids_cache

            self.mock_calculate_player_score = mock_calculate_player_score
            self.mock_calculate_player_score.return_value = 25.5

            yield

    def test_returns_player_info_and_score(self):
        """Test returns True with player info and score for valid player."""
        week_data = {"4046": {"gp": 1.0, "pass_yd": 300}}
        final_week_scores = {"QB": {}, "RB": {}, "DEF": {}}

        apply, info, score, pid = get_player_info_and_score(
            "4046", week_data, final_week_scores, {}
        )

        assert apply is True
        assert info["full_name"] == "Patrick Mahomes"
        assert score == 25.5
        assert pid == "4046"

    def test_returns_false_for_unknown_player(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test returns False for player not in player_ids_cache.

        Args:
            caplog: pytest caplog fixture
        """
        week_data = {"9999": {"gp": 1.0}}
        final_week_scores = {"QB": {}}

        with caplog.at_level(logging.WARNING):
            apply, _, _, _ = get_player_info_and_score(
                "9999", week_data, final_week_scores, {}
            )

        assert apply is False
        assert "Unknown numeric player id" in caplog.text

    def test_returns_false_for_numeric_def_player(self):
        """Test returns False for numeric player ID with DEF position."""
        self.mock_player_ids_cache["12345"] = {
            "full_name": "Some Defense",
            "position": "DEF",
        }
        week_data = {"12345": {"gp": 1.0}}
        final_week_scores = {"QB": {}, "DEF": {}}

        apply, _, _, _ = get_player_info_and_score(
            "12345", week_data, final_week_scores, {}
        )

        assert apply is False

    def test_returns_false_for_zero_games_played(self):
        """Test returns False when player has gp=0."""
        week_data = {"4046": {"gp": 0.0}}
        final_week_scores = {"QB": {}}

        apply, _, _, _ = get_player_info_and_score(
            "4046", week_data, final_week_scores, {}
        )

        assert apply is False

    def test_returns_false_for_position_not_in_final_scores(self):
        """Test returns False when position not in final_week_scores."""
        week_data = {"4046": {"gp": 1.0}}
        final_week_scores = {"RB": {}}

        apply, _, _, _ = get_player_info_and_score(
            "4046", week_data, final_week_scores, {}
        )

        assert apply is False

    def test_handles_ertz_edge_case_numeric_only(
        self, caplog: pytest.LogCaptureFixture
    ):
        """Test handles Zach Ertz edge case with non-numeric chars in ID.

        Args:
            caplog: pytest caplog fixture
        """
        self.mock_player_ids_cache["1234"] = {
            "full_name": "Zach Ertz",
            "position": "TE",
        }
        week_data = {"1234a": {"gp": 1.0, "rec_yd": 50}}
        final_week_scores = {"TE": {}}

        with caplog.at_level(logging.INFO):
            apply, _, _, pid = get_player_info_and_score(
                "1234a", week_data, final_week_scores, {}
            )

        assert apply is True
        assert pid == "1234"
        assert "removing the non-numeric" in caplog.text

    def test_ertz_edge_case_skips_when_real_id_exists(self):
        """Test skips modified ID when the real ID already exists."""
        self.mock_player_ids_cache["1234"] = {
            "full_name": "Zach Ertz",
            "position": "TE",
        }
        week_data = {
            "1234a": {"gp": 1.0},
            "1234": {"gp": 1.0},
        }
        final_week_scores = {"TE": {}}

        apply, _, _, _ = get_player_info_and_score(
            "1234a", week_data, final_week_scores, {}
        )

        assert apply is False

    def test_non_numeric_def_passes_through(self):
        """Test non-numeric DEF player ID passes through normally."""
        week_data = {"SEA": {"gp": 1.0, "def_td": 2}}
        final_week_scores = {"QB": {}, "DEF": {}}

        apply, info, _, _ = get_player_info_and_score(
            "SEA", week_data, final_week_scores, {}
        )

        assert apply is True
        assert info["position"] == "DEF"
