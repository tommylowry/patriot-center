"""This module provides utility functions for updating the image URLs cache."""

import logging
from copy import deepcopy
from time import time

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import NAME_TO_MANAGER_USERNAME
from patriot_center_backend.utils.sleeper_helpers import fetch_sleeper_data

logger = logging.getLogger(__name__)


def update_image_urls_cache(
    item: str, item_dict: dict[str, str | float], immediate_update: bool = False
) -> None:
    """Updates the image URLs cache with the given item and item_dict.

    Args:
        item: The item to update in the cache (e.g. manager name).
        item_dict: A dictionary containing the item's information (e.g. image
            URL and timestamp).
        immediate_update: If True, saves the updated cache to disk immediately.
    """
    image_urls_cache = CACHE_MANAGER.get_image_urls_cache()

    image_urls_cache[item] = item_dict

    if immediate_update:
        CACHE_MANAGER.save_image_urls_cache(image_urls_cache)


def get_image_url(item: str, dictionary: bool = False) -> dict[str, str] | str:
    """Get the image URL for a given item.

    This function checks if the item is a manager, draft pick, FAAB, or
    player. If it is a manager, it fetches the manager's image URL
    from the Sleeper API. If it is a draft pick, FAAB, or player, it
    returns the corresponding image URL.

    Args:
        item: The item to get the image URL for.
        dictionary: If True, return a dictionary containing the item's
            information. If False, return the item's image URL as a string.

    Returns:
        The item's image URL if found, otherwise an empty
            string. If dictionary is True, it returns a dictionary containing
            the item's information. If dictionary is False, it returns the
            item's image URL as a string.
    """
    image_urls_cache = CACHE_MANAGER.get_image_urls_cache()
    item_dict = {}

    # Manager: identified by presence in manager username mapping
    if item in NAME_TO_MANAGER_USERNAME:

        # Check to see if manager image URL is already in cache
        # if it is, and its less than one hour old, return it,
        # otherwise fetch it
        item_entry = image_urls_cache.get(item)
        update_item = (
            not item_entry or float(item_entry["timestamp"]) + 3600 < time()
        )

        if update_item:
            item_dict["name"] = item
            item_dict["image_url"] = get_current_manager_image_url(item)
            item_dict["timestamp"] = time()

            update_image_urls_cache(
                item, deepcopy(item_dict), immediate_update=True
            )

        # Return dict if dictionary=True and remove timestamp
        returning_dict = deepcopy(item_dict)
        returning_dict.pop("timestamp")
        return (
            deepcopy(returning_dict) if dictionary
            else returning_dict["image_url"]
        )


    # Draft Pick: identified by "Draft Pick" in name
    if "Draft Pick" in item:
        abridged_name = item.replace(" Draft Pick", "")
        abridged_name = abridged_name.replace("Round ", "R")
        first_name = abridged_name.split(" ")[0]
        last_name = abridged_name.replace(f"{first_name} ", "")
        item_dict["image_url"] = (
            "https://upload.wikimedia.org/wikipedia/en/thumb/8/80"
            "/NFL_Draft_logo.svg/1200px-NFL_Draft_logo.svg.png"
        )

        item_dict["name"] = item
        item_dict["first_name"] = first_name
        item_dict["last_name"] = last_name

        update_image_urls_cache(item, deepcopy(item_dict))
        return deepcopy(item_dict) if dictionary else item_dict["image_url"]

    # FAAB: identified by "$" in name
    if "$" in item:
        first_name = item.split(" ")[0]
        last_name = item.split(" ")[1]
        item_dict["image_url"] = (
            "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"
        )

        item_dict["name"] = item
        item_dict["first_name"] = first_name
        item_dict["last_name"] = last_name

        update_image_urls_cache(item, deepcopy(item_dict))
        return deepcopy(item_dict) if dictionary else item_dict["image_url"]

    players_cache = CACHE_MANAGER.get_players_cache()
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    # Player: identified by presence in players cache
    player = players_cache.get(item)

    # player_id is ether the item or the player's player_id
    player_id = item if not player else player.get("player_id")

    if player_id and player_id in player_ids_cache:

        # Numeric IDs are individual players (use player headshots)
        if player_id.isnumeric():
            url = (
                f"https://sleepercdn.com/content/"
                f"nfl/players/{player_id}.jpg"
            )

        # Non-numeric IDs are team defenses (use team logos)
        else:
            url = (
                f"https://sleepercdn.com/images/"
                f"team_logos/nfl/{player_id.lower()}.png"
            )

        item_dict["name"] = item
        item_dict["image_url"] = url
        item_dict["first_name"] = player_ids_cache[player_id]["first_name"]
        item_dict["last_name"] = player_ids_cache[player_id]["last_name"]

        update_image_urls_cache(item, deepcopy(item_dict))
        return deepcopy(item_dict) if dictionary else item_dict["image_url"]

    # If no match, return empty string
    logger.warning(f"Could not find image URL for item: {item}")
    return ""


def get_current_manager_image_url(manager: str) -> str:
    """Get the current manager's image URL from the Sleeper API.

    Args:
        manager: Manager name

    Returns:
        The current manager's image URL if found, otherwise an empty string.
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    user_id = (
        manager_cache.get(manager, {}).get("summary", {}).get("user_id", "")
    )

    if not user_id:
        logger.warning(
            f"Manager {manager} does not have a user_id in manager_cache."
        )
        return ""

    # Fetch the user data from the Sleeper API and ensure it's in dict form
    sleeper_data = fetch_sleeper_data(f"user/{user_id}")
    if not isinstance(sleeper_data, dict):
        logger.warning(
            f"Sleeper API call failed to retrieve "
            f"user data for manager {manager}."
        )
        return ""

    if "avatar" not in sleeper_data:
        logger.warning(
            f"Manager {manager} does not have an avatar in sleeper_data."
        )
        return ""

    return f"https://sleepercdn.com/avatars/{sleeper_data['avatar']}"
