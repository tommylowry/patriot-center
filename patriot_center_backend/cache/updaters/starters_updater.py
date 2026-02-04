"""This module provides utility functions for updating the starters cache."""

import logging
from decimal import Decimal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.domains.player import Player

logger = logging.getLogger(__name__)


def update_starters_cache(
    year: int,
    week: int,
    manager: str,
    player_id: str,
    player_score: float,
) -> None:
    """Update starters cache.

    Args:
        year: The NFL season year (e.g., 2024).
        week: The week number (1-17).
        manager: Manager name
        player_id: Player ID
        player_score: Player score
    """
    starters_cache = CACHE_MANAGER.get_starters_cache()

    # Update the cache if needed
    year_data = starters_cache.setdefault(str(year), {})
    week_data = year_data.setdefault(str(week), {})
    manager_data = week_data.setdefault(manager, {})

    manager_data.setdefault("Total_Points", 0.0)

    # Get player data
    player = Player(player_id)

    # Skip if player already exists
    if str(player) in manager_data:
        logger.warning(
            f"Duplicate player: {player} for manager: "
            f"{manager} in year: {year}, week: {week}"
        )
        return

    # Update total points
    total_points = manager_data["Total_Points"] + player_score
    manager_data["Total_Points"] = float(
        Decimal(total_points).quantize(Decimal("0.01")).normalize()
    )

    # Add player
    manager_data[str(player)] = {
        "points": player_score,
        "position": player.position,
        "player_id": player_id,
    }
