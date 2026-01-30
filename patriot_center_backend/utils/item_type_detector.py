"""Detects the type of item based on its name."""

from typing import Literal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import NAME_TO_MANAGER_USERNAME


def detect_item_type(
    item: str
) -> Literal["manager", "draft_pick", "faab", "player", "player_id", "unknown"]:
    """Detects the type of item based on its name.

    Args:
        item: Item to detect type for

    Returns:
        Type of item
    """
    # Manager: identified by presence in manager username mapping
    if item in NAME_TO_MANAGER_USERNAME:
        return "manager"

    # Draft Pick: identified by "Draft Pick" in name
    if "Draft Pick" in item:
        return "draft_pick"

    # FAAB: identified by "$" in name
    if "$" in item:
        return "faab"

    players_cache = CACHE_MANAGER.get_players_cache()
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    # Player: identified by presence in players cache
    if item in players_cache:
        return "player"

    if item in player_ids_cache:
        return "player_id"

    return "unknown"
