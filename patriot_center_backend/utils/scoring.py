"""This module provides utility functions for calculating player scores."""

from collections.abc import Mapping


def calculate_player_score(
    player_data: Mapping[str, int | float],
    scoring_settings: Mapping[str, int | float]
) -> float:
    """Calculate player score based on raw stats and scoring settings.

    This function takes in a dictionary of raw stats for a player and a
    dictionary of scoring settings for a league, and calculates the
    player's score based on the scoring settings.

    Args:
        player_data: Raw stats for a player. The dictionary should
            contain keys for each stat type and values for the number of
            units of each stat type. This dictionary should contain raw stats
            for each stat type.
        scoring_settings: Scoring settings for a league. The dictionary
            should contain keys for each stat type and values for the points
            per unit for each stat type. This dictionary should contain points
            per unit for each stat type.

    Returns:
        Calculated player score rounded to 2 decimal places.
    """
    total_score = 0.0
    for stat_key, stat_value in player_data.items():
        if stat_key in scoring_settings:
            # Get the points per unit for this stat type
            points_per_unit = scoring_settings[stat_key]
            # Calculate the score for this stat type
            total_score += stat_value * points_per_unit

    # Round the total score to 2 decimal places
    return round(total_score, 2)
