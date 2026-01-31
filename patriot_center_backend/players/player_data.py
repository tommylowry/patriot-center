"""This module provides utility functions for player data."""

import logging
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.calculations.player_score_calculator import (
    calculate_player_score,
)

logger = logging.getLogger(__name__)


def get_player_info_and_score(
    player_id: str,
    week_data: dict[str, dict[str, Any]],
    final_week_scores: dict[str, Any],
    scoring_settings: dict[str, Any],
) -> tuple[bool, dict[str, Any], float, str]:
    """Get player information and score for a given player ID.

    Args:
        player_id: The player ID to get information and score for.
        week_data: The data for the current week.
        final_week_scores: The final scores for the current week.
        scoring_settings: The scoring settings for the current season.

    Returns:
        Tuple containing:
        - A boolean indicating whether the player was found.
        - A dictionary containing the player information.
        - A float representing the player score.
        - A string representing the player ID.
    """
    # Get player information

    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    # Zach Ertz traded from PHI to ARI causes his player ID to be weird
    # sometimes
    if player_id not in player_ids_cache:
        only_numeric = "".join(c for c in player_id if c.isnumeric())
        if only_numeric in player_ids_cache:
            if only_numeric in week_data:
                # skipping this player since his actual id is in player_ids
                # as to not double count
                return False, {}, 0.0, player_id

            player_name = player_ids_cache[only_numeric]["full_name"]
            logger.info(
                f"Encountered player id with numeric and non numeric chars "
                f"in sleeper's output of player data, removing the non-numeric "
                f"chars and using {player_name}, player-id {only_numeric} "
                f"instead of {player_id}"
            )
            player_info = player_ids_cache[only_numeric]
            player_data = week_data[player_id]
            player_id = only_numeric
        else:
            logger.warning(
                f"Unknown numeric player id encountered: {player_id}"
            )
            return False, {}, 0.0, player_id
    else:
        # Get player information from PLAYER_IDS
        player_info = player_ids_cache[player_id]
        player_data = week_data[player_id]

    # If the player ID is numeric and the position is DEF, skip processing
    if player_id.isnumeric() and player_info["position"] == "DEF":
        return False, {}, 0.0, player_id

    if player_info["position"] in list(final_week_scores.keys()):
        if player_data.get("gp", 0.0) == 0.0:
            return False, {}, 0.0, player_id

        player_score = calculate_player_score(player_data, scoring_settings)

        return True, player_info, player_score, player_id

    return False, {}, 0.0, player_id
