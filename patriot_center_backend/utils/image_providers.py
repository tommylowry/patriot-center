"""Image URL provider for Patriot Center."""

import logging
from copy import deepcopy

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import NAME_TO_MANAGER_USERNAME
from patriot_center_backend.utils.sleeper_helpers import fetch_sleeper_data

logger = logging.getLogger(__name__)


def get_image_url(
    item: str, image_urls: dict[str, str], dictionary: bool = False
) -> dict[str, str] | str:
    """Get image URL for various types (draft picks, FAAB, managers, players).

    Determines entity type from item string and returns appropriate image URL.
    Supports four entity types:
    - Draft picks: Draft logo
    - FAAB (contains "$"): Coin image
    - Managers: Sleeper avatar
    - Players: Sleeper player headshot or team logo

    Args:
        item: Entity name/identifier string
        image_urls: Dict of image URLs
        dictionary: If True, returns dict with name components;
            if False, returns URL string

    Returns:
        Image URL string, or dict with name/URL if `dictionary`=True
    """
    players_cache = CACHE_MANAGER.get_players_cache()
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    if dictionary:
        returning_dict = {"name": item, "image_url": ""}

    # Draft Pick: identified by "Draft Pick" in name
    if "Draft Pick" in item:
        if dictionary:
            abridged_name = item.replace(" Draft Pick", "")
            abridged_name = abridged_name.replace("Round ", "R")
            first_name = abridged_name.split(" ")[0]
            last_name = abridged_name.replace(f"{first_name} ", "")
            returning_dict["image_url"] = (
                "https://upload.wikimedia.org/wikipedia/en/thumb/8/80"
                "/NFL_Draft_logo.svg/1200px-NFL_Draft_logo.svg.png"
            )

            returning_dict["first_name"] = first_name
            returning_dict["last_name"] = last_name
            return deepcopy(returning_dict)
        return (
            "https://upload.wikimedia.org/wikipedia/en/thumb/8/80"
            "/NFL_Draft_logo.svg/1200px-NFL_Draft_logo.svg.png"
        )

    # FAAB: identified by "$" in name
    if "$" in item:
        if dictionary:
            first_name = item.split(" ")[0]
            last_name = item.split(" ")[1]
            returning_dict["image_url"] = (
                "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"
            )

            returning_dict["first_name"] = first_name
            returning_dict["last_name"] = last_name
            return deepcopy(returning_dict)
        return "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"

    # Manager: identified by presence in manager username mapping
    if item in NAME_TO_MANAGER_USERNAME:
        if dictionary:
            returning_dict["image_url"] = get_current_manager_image_url(
                item, image_urls
            )

            return deepcopy(returning_dict)
        return get_current_manager_image_url(item, image_urls)

    # Player: identified by presence in players cache
    player = players_cache.get(item)

    # player_id is ether the item or the player's player_id
    player_id = item if not player else player.get("player_id")

    if player_id and player_id in player_ids_cache:

        first_name = player_ids_cache[player_id]["first_name"]
        last_name = player_ids_cache[player_id]["last_name"]

        # Numeric IDs are individual players (use player headshots)
        if player_id.isnumeric():
            url = (
                f"https://sleepercdn.com/content/"
                f"nfl/players/{player_id}.jpg"
            )

            if dictionary:
                returning_dict["image_url"] = url
                returning_dict["first_name"] = first_name
                returning_dict["last_name"] = last_name
                return deepcopy(returning_dict)
            return url

        # Non-numeric IDs are team defenses (use team logos)
        else:
            url = (
                f"https://sleepercdn.com/images/"
                f"team_logos/nfl/{player_id.lower()}.png"
            )

            if dictionary:
                returning_dict["image_url"] = url
                returning_dict["first_name"] = first_name
                returning_dict["last_name"] = last_name
                return deepcopy(returning_dict)
            return url

    # If no match, return empty string
    logger.warning(f"Could not find image URL for item: {item}")
    return ""


def get_current_manager_image_url(
    manager: str, image_urls: dict[str, str]
) -> str:
    """Get current manager's avatar image URL.

    Args:
        manager: Manager name
        image_urls: Dict of image URLs (mutable, will be updated)

    Returns:
        Image URL string

    Raises:
        ValueError: If manager not found in manager cache
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    if manager in image_urls:
        return image_urls[manager]

    user_id = (
        manager_cache.get(manager, {}).get("summary", {}).get("user_id", "")
    )

    if not user_id:
        raise ValueError(
            f"Manager {manager} does not have a user_id in manager_cache."
        )

    # Fetch the user data from the Sleeper API and ensure it's in dict form
    sleeper_data = fetch_sleeper_data(f"user/{user_id}")
    user_payload = sleeper_data if isinstance(sleeper_data, dict) else {}

    if user_payload and "user_id" in user_payload:
        image_urls[manager] = (
            f"https://sleepercdn.com/avatars/{user_payload.get('avatar', '')}"
        )

        return (
            f"https://sleepercdn.com/avatars/{user_payload.get('avatar', '')}"
        )

    return ""
