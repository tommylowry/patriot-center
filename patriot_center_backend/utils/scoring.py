"""
This module provides utility functions for calculating player scores based on
raw stats and scoring settings.
"""

def calculate_player_score(player_data: dict, scoring_settings: dict) -> float:
    """
    Calculate player score based on raw stats and scoring settings.

    This function takes in a dictionary of raw stats for a player and a dictionary
    of scoring settings for a league, and calculates the player's score based on
    the scoring settings.

    Args:
        player_data (dict): Raw stats for a player.
        scoring_settings (dict): Scoring settings for a league.

    Returns:
        float: Calculated player score.

    Notes:
        - The scoring settings dictionary should contain keys for each stat type
          (e.g. 'passing_yards', 'rushing_yards', etc.) and values for the
          points per unit for each stat type.
        - The player data dictionary should contain keys for each stat type and
          values for the number of units of each stat type.
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
