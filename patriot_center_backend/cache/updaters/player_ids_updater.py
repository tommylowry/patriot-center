"""Player IDs loader and refresher for the Patriot Center backend.

This module:
- Updates the player IDs cache by fetching fresh data from Sleeper API.
- Inserts synthetic team defense entries as players with position "DEF".
"""

import logging
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.cache_synchronizer import CacheSynchronizer
from patriot_center_backend.utils.defense_helper import get_defense_entries
from patriot_center_backend.utils.sleeper_helpers import fetch_all_player_ids

logger = logging.getLogger(__name__)

# Fields to keep from Sleeper's player payload; reduces storage and surface area
FIELDS_TO_KEEP = [
    "full_name",
    "first_name",
    "last_name",
    "age",
    "years_exp",
    "college",
    "team",
    "depth_chart_position",
    "fantasy_positions",
    "position",
    "number",
]


def update_player_ids_cache() -> None:
    """Updates the player IDs cache.

    This function:
    - Checks if the player IDs cache is stale
    - Fetches fresh data from Sleeper API
    - Updates the player IDs cache
    """
    if not CACHE_MANAGER.is_player_ids_cache_stale():
        return  # cache is fresh, nothing to do

    new_player_ids_cache = {}

    # fetch fresh data from Sleeper API and populate the cache
    updated_sleeper_player_ids = fetch_all_player_ids()
    for player_id, player_info in updated_sleeper_player_ids.items():
        _add_player_id_entry(player_id, player_info, new_player_ids_cache)

    # Fill in historic team defense entries (OAK, SD, etc.)
    _fill_missing_defenses(new_player_ids_cache)

    # If players change their names they need to be
    # changed throughout every cache file.
    CacheSynchronizer(new_player_ids_cache).synchronize()

    # Save the new player IDs cache
    CACHE_MANAGER.save_player_ids_cache(new_player_ids_cache)


def _add_player_id_entry(
    player_id: str,
    player_info: dict[str, Any],
    new_player_ids_cache: dict[str, dict[str, Any]]
) -> None:
    """Adds a player ID entry to the player IDs cache.

    Args:
        player_id: The player ID
        player_info: The player info
        new_player_ids_cache: The new player IDs cache
    """
    _apply_full_name(player_info)
    new_player_ids_cache[player_id] = {
        key: player_info.get(key) for key in FIELDS_TO_KEEP
    }


def _apply_full_name(player_info: dict[str, Any]) -> None:
    """Applies a full name to the player info.

    Args:
        player_info: The player info
    """
    if "full_name" not in player_info:
        full_name = (
            f"{player_info.get('first_name', '')} "
            f"{player_info.get('last_name', '')}"
        )

        if full_name == " ":
            full_name = None

        player_info["full_name"] = full_name


def _fill_missing_defenses(
    new_player_ids_cache: dict[str, dict[str, Any]]
) -> None:
    """Fills in missing team defense entries (OAK, SD, etc.).

    Args:
        new_player_ids_cache: The new player IDs cache
    """
    defense_entries = get_defense_entries()

    for player_id, player_info in defense_entries.items():
        if player_id not in new_player_ids_cache:
            _add_player_id_entry(player_id, player_info, new_player_ids_cache)
