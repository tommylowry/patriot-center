"""Update valid options cache."""

import logging

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.domains.player import Player

logger = logging.getLogger(__name__)


def update_valid_options_cache(
    year: int, week: int, manager: str, player_id: str
) -> None:
    """Update valid options cache.

    This function updates the valid options cache with the provided data. It
    also updates the parent data levels (year, week, and manager) if needed.

    Args:
        year: The NFL season year (e.g., 2024).
        week: The week number (1-17).
        manager: Manager name
        player_id: Player ID
    """
    player = Player(player_id)

    update_valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    # Year level
    year_data = update_valid_options_cache.setdefault(
        str(year), {"managers": [], "players": [], "weeks": [], "positions": []}
    )
    _update_list(year_data["managers"], manager)
    _update_list(year_data["players"], str(player))
    _update_list(year_data["weeks"], str(week))
    _update_list(year_data["positions"], player.position)

    # Week level
    week_data = year_data.setdefault(
        str(week), {"managers": [], "players": [], "positions": []}
    )
    _update_list(week_data["managers"], manager)
    _update_list(week_data["players"], str(player))
    _update_list(week_data["positions"], player.position)

    # Manager level
    manager_data = week_data.setdefault(
        manager, {"players": [], "positions": []}
    )
    _update_list(manager_data["players"], str(player))
    _update_list(manager_data["positions"], player.position)


def _update_list(list_to_update: list[str], value: str) -> None:
    """Update list if value not already in it.

    Args:
        list_to_update: List to update
        value: Value to add
    """
    if value not in list_to_update:
        list_to_update.append(value)
