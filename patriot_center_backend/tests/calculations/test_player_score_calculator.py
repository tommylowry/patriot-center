"""Unit tests for player_score_calculator module."""

from patriot_center_backend.calculations.player_score_calculator import (
    calculate_player_score,
)


class TestCalculatePlayerScore:
    """Unit tests for the calculate_player_score function."""

    def test_simple_score(self):
        """Test returns the correct score for a simple case."""
        player_data = {"passing_yards": 300}
        scoring_settings = {"passing_yards": 0.04}

        result = calculate_player_score(player_data, scoring_settings)

        assert result == 12.0

    def test_multiple_stat_types(self):
        """Test returns the correct score with multiple stat types."""
        player_data = {"passing_yards": 300, "rushing_yards": 100}
        scoring_settings = {"passing_yards": 0.04, "rushing_yards": 0.02}

        result = calculate_player_score(player_data, scoring_settings)

        assert result == 14.0

    def test_zero_stat_value(self):
        """Test returns 0 when the stat value is 0."""
        player_data = {"passing_yards": 0}
        scoring_settings = {"passing_yards": 0.04}

        result = calculate_player_score(player_data, scoring_settings)

        assert result == 0.0

    def test_missing_stat_type(self):
        """Test returns 0 when the stat type is not in the scoring settings."""
        player_data = {"passing_yards": 300}
        scoring_settings = {"rushing_yards": 0.02}

        result = calculate_player_score(player_data, scoring_settings)

        assert result == 0.0

    def test_rounding(self):
        """Test  returns the correct score when rounding is needed."""
        player_data = {"passing_yards": 1056}
        scoring_settings = {"passing_yards": 0.1}

        result = calculate_player_score(player_data, scoring_settings)

        assert result == 105.6
