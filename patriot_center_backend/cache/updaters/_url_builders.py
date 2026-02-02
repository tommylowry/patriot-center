"""This module provides utility functions for building URLs."""

import logging
from time import time

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.utils.helpers import get_player_id, get_player_name
from patriot_center_backend.utils.sleeper_helpers import fetch_user_metadata

logger = logging.getLogger(__name__)


def build_manager_url(manager_name: str) -> dict[str, str]:
    """Builds a URL for a manager.

    Args:
        manager_name: The name of the manager.

    Returns:
        A dictionary containing the name, image URL, and timestamp.
    """
    user_metadata = fetch_user_metadata(manager_name, bypass_cache=True)

    avatar = user_metadata.get("avatar")
    if not avatar:
        logger.warning(
            f"Manager {manager_name} does not have an avatar in sleeper data."
        )
        return {}

    url = f"https://sleepercdn.com/avatars/{avatar}"

    output = {
        "name": manager_name,
        "image_url": url,
        "timestamp": time(),
    }

    return output


def build_draft_pick_url(draft_pick_name: str) -> dict[str, str]:
    """Builds a URL for a draft pick.

    Args:
        draft_pick_name: The name of the draft pick.

    Returns:
        A dictionary containing the name, image URL, first name, and last name.
    """
    abridged_name = draft_pick_name.replace(" Draft Pick", "")
    abridged_name = abridged_name.replace("Round ", "R")

    first_name = abridged_name.split(" ")[0]
    last_name = abridged_name.replace(f"{first_name} ", "")

    output = {
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/en/thumb/8/80"
            "/NFL_Draft_logo.svg/1200px-NFL_Draft_logo.svg.png"
        ),
        "name": draft_pick_name,
        "first_name": first_name,
        "last_name": last_name,
    }

    return output


def build_faab_url(item: str) -> dict[str, str]:
    """Builds a URL for a FAAB player.

    Args:
        item: The name of the FAAB player.

    Returns:
        A dictionary containing the name, image URL, first name, and last name.
    """
    first_name = item.split(" ")[0]
    last_name = item.split(" ")[1]

    output = {
        "image_url": (
            "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"
        ),
        "name": item,
        "first_name": first_name,
        "last_name": last_name,
    }

    return output


def build_player_id_url(player_id: str) -> dict[str, str]:
    """Builds a URL for a player ID.

    Args:
        player_id: The ID of the player.

    Returns:
        A dictionary containing the name, image URL, first name, and last name.
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    if player_id.isnumeric():
        url = f"https://sleepercdn.com/content/nfl/players/{player_id}.jpg"
    else:
        url = (
            f"https://sleepercdn.com/images/"
            f"team_logos/nfl/{player_id.lower()}.png"
        )

    full_name = get_player_name(player_id)
    if not full_name:
        logger.warning(
            f"Player {player_id} does not have a full name in player_ids_cache."
        )
        return {}

    first_name = player_ids_cache.get(player_id, {}).get("first_name", "")
    last_name = player_ids_cache.get(player_id, {}).get("last_name", "")

    output = {
        "name": full_name,
        "image_url": url,
        "first_name": first_name,
        "last_name": last_name,
    }

    return output


def build_player_url(player_name: str) -> dict[str, str]:
    """Builds a URL for a player.

    Args:
        player_name: The name of the player.

    Returns:
        A dictionary containing the name, image URL, first name, and last name.
    """
    player_id = get_player_id(player_name)
    if not player_id:
        logger.warning(
            f"Player {player_name} does not have "
            f"a player_id in player_ids_cache."
        )
        return {}

    return build_player_id_url(player_id)


def build_url(item: str, item_type: str) -> dict[str, str]:
    """Builds a URL based on the item type.

    Args:
        item: The item for which to build the URL.
        item_type: The type of the item.

    Returns:
        A dictionary containing the name, image URL, first name, and last name.
    """
    url_builders = {
        "manager": build_manager_url,
        "draft_pick": build_draft_pick_url,
        "faab": build_faab_url,
        "player_id": build_player_id_url,
        "player": build_player_url,
    }

    return url_builders[item_type](item)
