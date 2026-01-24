"""This module provides utility functions for updating the image URLs cache."""

import logging
from copy import deepcopy
from time import time
from typing import cast

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import NAME_TO_MANAGER_USERNAME
from patriot_center_backend.utils.sleeper_helpers import fetch_sleeper_data

logger = logging.getLogger(__name__)


def update_image_urls_cache(item: str) -> dict[str, str]:
    """Update the image URLs cache.

    Args:
        item: Item to update

    Returns:
        Updated image URLs cache
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
            item_dict["image_url"] = _get_current_manager_image_url(item)
            item_dict["timestamp"] = time()

            image_urls_cache[item] = item_dict
            CACHE_MANAGER.save_image_urls_cache(image_urls_cache)

        # Return dict if dictionary=True and remove timestamp
        returning_dict = deepcopy(item_dict)
        if "timestamp" in returning_dict:
            returning_dict.pop("timestamp")

        return deepcopy(returning_dict)


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

        image_urls_cache[item] = item_dict
        return deepcopy(item_dict)

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

        image_urls_cache[item] = item_dict
        return deepcopy(item_dict)

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

        image_urls_cache[item] = item_dict
        return deepcopy(item_dict)

    # If no match, return empty string
    logger.warning(f"Could not find image URL for item: {item}")
    return {}



def get_image_url(item: str, dictionary: bool = False) -> dict[str, str] | str:
    """Get image URL for item.

    Args:
        item: Item to get image URL for
        dictionary: If True, return dictionary with other values, otherwise
            return string

    Returns:
        Image URL for item
            or dictionary of image URL, name, first name, and last name
    """
    image_urls_cache = CACHE_MANAGER.get_image_urls_cache()

    if item in NAME_TO_MANAGER_USERNAME:
        manager_result = update_image_urls_cache(item)

        return (
            deepcopy(manager_result)
            if dictionary
            else manager_result["image_url"]
        )

    if item in image_urls_cache:
        image_url = image_urls_cache[item].get("image_url")

        if not isinstance(image_url, str):
            logger.warning(
                f"Image URL for {item} is not a string: {image_url}"
            )

            del image_urls_cache[item]
            return get_image_url(item, dictionary=dictionary)

        if dictionary:
            returning_dict = deepcopy(image_urls_cache[item])

            # Remove timestamp before returning so only string values
            # are returned
            returning_dict.pop("timestamp", None)
            return cast(dict[str, str], returning_dict)
        else:
            return image_url

    url_result = update_image_urls_cache(item)

    return (
        deepcopy(url_result)
        if dictionary
        else url_result["image_url"]
    )


def _get_current_manager_image_url(manager: str) -> str:
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
