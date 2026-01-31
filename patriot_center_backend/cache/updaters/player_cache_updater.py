"""This module provides utility functions for updating the players cache."""

import logging
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters.image_urls_updater import (
    update_image_urls_cache,
)
from patriot_center_backend.utils.slug_utils import slugify

logger = logging.getLogger(__name__)


def update_players_cache(player_id: str) -> None:
    """Updates the players cache if applicable.

    This function updates the players cache by adding a new player if
        the player_id is present in the player_ids cache.

    Args:
        player_id: The ID of the player to add to the cache.
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()
    players_cache = CACHE_MANAGER.get_players_cache()

    player_name = player_ids_cache.get(player_id, {}).get("full_name", "")

    if not player_name:
        logger.warning(f"player_id {player_id} not found in player_ids")
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
            "player_id": player_id,
        }

        update_image_urls_cache(player_meta["full_name"])
        update_image_urls_cache(player_id)


def update_players_cache_with_list(item: list[dict[str, Any]]) -> None:
    """Updates the players cache with a list of matchup dictionaries.

    This function updates the players cache by adding new players from a
        list of matchup dictionaries if the player_ids are present in the
        player_ids cache and the players are not already in the players cache.

    Args:
        item: A list of matchup dictionaries,
            each containing a 'players' key with a list of player_ids.
    """
    if not isinstance(item, list):
        logging.warning(
            "Item inputted into update_players_cache_with_list is not a list."
        )
        return

    called = False
    for matchup in item:
        if not isinstance(matchup, dict):
            continue
        for player_id in matchup.get("players", ""):
            called = True
            update_players_cache(player_id)

    if not called:
        logger.warning(
            "Item inputted into update_players_cache_with_list"
            "did not have a matchup dict with players."
        )
