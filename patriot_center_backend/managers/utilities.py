"""
Utility helpers for manager metadata processing.

Standalone functions for common operations like image URL generation,
draft pick parsing, and player cache management.
"""
from copy import deepcopy
from typing import Dict, Any

from patriot_center_backend.constants import NAME_TO_MANAGER_USERNAME
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data


def draft_pick_decipher(draft_pick_dict: Dict[str, Any], weekly_roster_ids: Dict[int, str]) -> str:
    """
    Decipher draft pick string to manager name.

    Example draft_pick_dict:
    {
        "season": "2019", # the season this draft pick belongs to
        "round": 5,       # which round this draft pick is
        "roster_id": 1,   # original owner's roster_id
        "previous_owner_id": 1,  # previous owner's roster id (in this trade)
        "owner_id": 2,    # the new owner of this pick after the trade
    }
    
    Args:
        draft_pick_dict:   Sleeper traded draft pick data
        weekly_roster_ids: Mapping of roster IDs to manager names
    
    Returns:
        Manager name or "Unknown Manager"
    """
    season = draft_pick_dict.get("season", "unknown_year")
    round_num = draft_pick_dict.get("round", "unknown_round")

    origin_team = draft_pick_dict.get("roster_id", "unknown_team")
    origin_manager = weekly_roster_ids.get(origin_team, "unknown_manager")

    return f"{origin_manager}'s {season} Round {round_num} Draft Pick"


def extract_dict_data(data: dict, players_cache: dict, player_ids: dict,
                     image_urls_cache: dict, cache: dict,
                     key_name: str = "name", value_name: str = "count",
                     cutoff: int = 3) -> list:
    """
    Extract top N items from a dictionary and format with image URLs.

    Handles tie-breaking logic to include all items tied for the cutoff position.
    For example, if cutoff=3 and items 3-5 are tied, all will be included.

    Args:
        data: Raw data dictionary (may contain nested dicts with "total" keys)
        players_cache: Cache of player metadata
        player_ids: Player ID to metadata mapping
        image_urls_cache: Cache of image URLs
        cache: Full manager cache
        key_name: Name of the key field in output (default: "name")
        value_name: Name of the value field in output (default: "count")
        cutoff: Number of top items to include (0 means all items)

    Returns:
        List of dictionaries with key_name, value_name, and image_url fields
    """
    # Flatten nested dictionaries by extracting "total" values
    for key in data:
        if not isinstance(data[key], dict):
            break
        data[key] = data[key]["total"]

    # Sort items by value in descending order
    sorted_items = sorted(data.items(), key=lambda item: item[1], reverse=True)

    # If no cutoff, include all items
    if not cutoff:
        top_three = dict(sorted_items)
    else:
        # Handle ties at the cutoff position
        # Start at cutoff position (e.g., index 2 for top 3)
        i = min(cutoff-1, len(sorted_items) - 1)
        # Extend cutoff to include all tied items
        for j in range(i, len(sorted_items) - 1):
            if sorted_items[j][1] != sorted_items[j+1][1]:
                i = j
                break
            i = j + 1
        top_three = dict(sorted_items[:i+1])

    # Build formatted output list with image URLs
    items = []
    for item in top_three:
        long_dict = {}
        long_dict[key_name] = item
        long_dict[value_name] = top_three[item]
        long_dict["image_url"] = get_image_url(item, players_cache, player_ids,
                                      image_urls_cache, cache)
        items.append(deepcopy(long_dict))

    return deepcopy(items)


def get_image_url(item: str, players_cache: dict, player_ids: dict,
                  image_urls_cache: dict, cache: dict, dictionary: bool = False) -> str:
    """
    Get image URL for various entity types (draft picks, FAAB, managers, players).

    Determines entity type from item string and returns appropriate image URL.
    Supports four entity types:
    - Draft picks: NFL Draft logo
    - FAAB (contains "$"): Mario coin image
    - Managers: Sleeper avatar
    - Players: Sleeper player headshot or team logo

    Args:
        item: Entity name/identifier string
        players_cache: Cache of player data
        player_ids: Player ID to metadata mapping
        image_urls_cache: Cache of image URLs
        cache: Full manager cache
        dictionary: If True, returns dict with name components; if False, returns URL string

    Returns:
        Image URL string, or dict with name/URL if dictionary=True
    """
    if dictionary:
        returning_dict = {"name": item, "image_url": ""}

    # Draft Pick: identified by "Draft Pick" in name
    if "Draft Pick" in item:
        if dictionary:
            abridged_name = item.replace(" Draft Pick", "")
            abridged_name = abridged_name.replace("Round ", "R")
            first_name = abridged_name.split(" ")[0]
            last_name  = abridged_name.replace(f"{first_name} ", "")
            returning_dict["image_url"] = "https://upload.wikimedia.org/wikipedia/en/thumb/8/80/NFL_Draft_logo.svg/1200px-NFL_Draft_logo.svg.png"
            returning_dict["first_name"] = first_name
            returning_dict["last_name"]  = last_name
            return deepcopy(returning_dict)
        return "https://upload.wikimedia.org/wikipedia/en/thumb/8/80/NFL_Draft_logo.svg/1200px-NFL_Draft_logo.svg.png"

    # FAAB: identified by "$" in name
    if "$" in item:
        if dictionary:
            first_name = item.split(" ")[0]
            last_name =  item.split(" ")[1]
            returning_dict["image_url"]  = "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"
            returning_dict["first_name"] = first_name
            returning_dict["last_name"]  = last_name
            return deepcopy(returning_dict)
        return "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"

    # Manager: identified by presence in manager username mapping
    if item in NAME_TO_MANAGER_USERNAME:
        if dictionary:
            returning_dict["image_url"] = get_current_manager_image_url(item, cache, image_urls_cache)
            return deepcopy(returning_dict)
        return get_current_manager_image_url(item, cache, image_urls_cache)

    # Player: identified by presence in players cache
    if item in players_cache:
        player_id = players_cache[item]["player_id"]
        first_name = player_ids[player_id]['first_name']
        last_name = player_ids[player_id]['last_name']
        # Numeric IDs are individual players (use player headshots)
        if player_id.isnumeric():
            url = f"https://sleepercdn.com/content/nfl/players/{player_id}.jpg"
            if dictionary:
                returning_dict["image_url"] = url
                returning_dict["first_name"] = first_name
                returning_dict["last_name"]  = last_name
                return deepcopy(returning_dict)
            return url
        # Non-numeric IDs are team defenses (use team logos)
        else:
            url = f"https://sleepercdn.com/images/team_logos/nfl/{player_id.lower()}.png"
            if dictionary:
                returning_dict["image_url"] = url
                returning_dict["first_name"] = first_name
                returning_dict["last_name"]  = last_name
                return deepcopy(returning_dict)
            return url

    print("WARNING: Could not find image URL for item:", item)
    return ""


def get_current_manager_image_url(manager: str, cache: dict, 
                                  image_urls_cache: dict) -> str:
    """
    Get current manager's avatar image URL.
    
    Args:
        manager: Manager name
        cache: Full manager cache
        image_urls_cache: Cache of image URLs (mutable, will be updated)
    
    Returns:
        Image URL string
    """
    if manager in image_urls_cache:
        return image_urls_cache[manager]

    user_id = cache.get(manager, {}).get("summary", {}).get("user_id", "")

    user_payload, status_code = fetch_sleeper_data(f"user/{user_id}")
    if status_code == 200 and user_payload and "user_id" in user_payload:
        image_urls_cache[manager] = f"https://sleepercdn.com/avatars/{user_payload.get('avatar','')}"
        return f"https://sleepercdn.com/avatars/{user_payload.get('avatar','')}"

    return ""


def update_players_cache(item: list|str, players_cache: dict,
                         player_ids: dict) -> None:
    """
    Update players cache with player metadata from matchup data or individual player ID.

    Adds player metadata including full name, position, team, and URL slug.
    Supports two input modes:
    - List: Process all players from matchup data
    - String: Process a single player ID

    Args:
        item: Either list of matchup data or single player_id string
        players_cache: Existing player cache (will be modified in-place)
        player_ids: Player ID to metadata mapping

    Returns:
        None (modifies players_cache in-place)

    Raises:
        ValueError: If item is None or empty, or if wrong type provided
    """
    if not item:
            raise ValueError("Item to update players cache cannot be None or empty.")

    # Handle single player ID
    if isinstance(item, str):
        player_name = player_ids.get(item, {}).get("full_name", "")

        if player_name not in players_cache:
            player_meta = player_ids.get(item, {})

            # Create URL-encoded slug for player name (for API/URL usage)
            slug = player_meta.get("full_name", "").lower()
            slug = slug.replace(" ", "%20")
            slug = slug.replace("'", "%27")
            
            players_cache[player_meta["full_name"]] = {
                "full_name": player_meta.get("full_name", ""),
                "first_name": player_meta.get("first_name", ""),
                "last_name": player_meta.get("last_name", ""),
                "position": player_meta.get("position", ""),
                "team": player_meta.get("team", ""),
                "slug": slug,
                "player_id": item
            }


        return

    # Handle list of matchup data
    elif isinstance(item, list):
        for matchup in item:
            for player_id in matchup['players']:
                player_meta = player_ids.get(player_id, {})

                player_meta = deepcopy(player_meta)
                player_meta["player_id"] = player_id

                if player_meta.get("full_name") not in players_cache:

                    # Create URL-encoded slug for player name
                    slug = player_meta.get("full_name", "").lower()
                    slug = slug.replace(" ", "%20")
                    slug = slug.replace("'", "%27")
                    
                    players_cache[player_meta["full_name"]] = {
                        "full_name": player_meta.get("full_name", ""),
                        "first_name": player_meta.get("first_name", ""),
                        "last_name": player_meta.get("last_name", ""),
                        "position": player_meta.get("position", ""),
                        "team": player_meta.get("team", ""),
                        "slug": slug,
                        "player_id": player_id
                    }
        
        return
    
    raise ValueError("Either matchups or player_id must be provided to update players cache.")