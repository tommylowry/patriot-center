"""
Calculate a player's total fantasy score based on their stats and league scoring settings.

Iterates through all stats in player_data and multiplies each stat value by its
corresponding points-per-unit value from scoring_settings. Only stats that exist
in the scoring_settings are counted.
"""

def calculate_player_score (player_data: dict, scoring_settings: dict) -> float:
    """
    Args:
        player_data (dict): Player's raw stats for the week.
            Example: {"pass_yd": 300, "pass_td": 3, "rush_yd": 20, "gp": 1}

        scoring_settings (dict): League's scoring rules mapping stat keys to point values.
            Example: {"pass_yd": 0.04, "pass_td": 4, "rush_yd": 0.1}

    Returns:
        float: The player's total fantasy points, rounded to 2 decimal places.

    Example:
        >>> player_data = {"pass_yd": 300, "pass_td": 2, "gp": 1}
        >>> scoring_settings = {"pass_yd": 0.04, "pass_td": 4}
        >>> _calculate_player_score(player_data, scoring_settings)
        20.0  # (300 * 0.04) + (2 * 4) = 12 + 8 = 20.0

    Notes:
        - Stats not in scoring_settings are ignored (e.g., "gp", "player_id").
        - Supports negative point values (e.g., interceptions: -2 per int).
        - Always rounds to exactly 2 decimal places.
    """
    total_score = 0.0
    for stat_key, stat_value in player_data.items():

        if stat_key in scoring_settings:
            points_per_unit = scoring_settings[stat_key]
            total_score += stat_value * points_per_unit
    return round(total_score, 2)