"""
This module provides utility functions for updating the players cache.
"""
from typing import Any, Dict, List

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.utils.slug_utils import slugify


def update_players_cache(player_id: str) -> None:
    """
    Update players cache with player metadata from individual player ID.

    Adds player metadata including full name, position, team, and URL slug.

    Args:
        item: Single player_id string

    Returns:
        None (modifies players_cache in-place)
    """    
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()
    players_cache    = CACHE_MANAGER.get_players_cache()

    player_name = player_ids_cache.get(player_id, {}).get("full_name", "")
    
    if player_name == "":
        print(f"WARNING: player_id {player_id} not found in player_ids")
        return

    if player_name not in players_cache:

        player_meta = player_ids_cache.get(player_id, {})

        players_cache[player_meta["full_name"]] = {
            "full_name": player_meta.get("full_name", ""),
            "first_name": player_meta.get("first_name", ""),
            "last_name": player_meta.get("last_name", ""),
            "position": player_meta.get("position", ""),
            "team": player_meta.get("team", ""),
            "slug": slugify(player_meta.get("full_name", "")),
            "player_id": player_id
        }

def update_players_cache_list(item: List[Dict[str, Any]]):
    """
    Update players cache with a list of player metadata.

    Args:
        item: List of dictionaries containing player metadata.

    Returns:
        None (modifies players_cache in-place)
    """

    if not isinstance(item, list):
        print("WARNING: Item inputted into update_players_cache_list is not a list.")
        return
    
    for matchup in item:
        for player_id in matchup['players']:
            update_players_cache(player_id)