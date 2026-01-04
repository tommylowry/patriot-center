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
    Extract and format dictionary data with image URLs.

    
    Args:
        data: Raw data dictionary
        manager: Manager name
        image_urls_cache: Cache of image URLs
        cache: Full manager cache
    
    Returns:
        Formatted data dictionary with image URLs
    """
    for key in data:
        if not isinstance(data[key], dict):
            break
        data[key] = data[key]["total"]
    
    
    sorted_items = sorted(data.items(), key=lambda item: item[1], reverse=True)

    # not cutoff means include all
    if not cutoff:
        top_three = dict(sorted_items)
    else:
        # Handle ties for third place
        i = min(cutoff-1, len(sorted_items) - 1)  # Start at index 2 or last index, whichever is smaller
        for j in range(i, len(sorted_items) - 1):
            if sorted_items[j][1] != sorted_items[j+1][1]:
                i = j
                break
            i = j + 1
        top_three = dict(sorted_items[:i+1])

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
    Get player image URL from cache or Sleeper API.
    
    Args:
        player_id: Player ID string
        players_cache: Cache of player data
        player_ids: Player ID mapping
        image_urls_cache: Cache of image URLs
    
    Returns:
        Image URL string or empty string if not found
    """
    if dictionary:
        returning_dict = {"name": item, "image_url": ""}

    # Draft Pick
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
    
    # FAAB
    if "$" in item:
        if dictionary:
            first_name = item.split(" ")[0]
            last_name =  item.split(" ")[1]
            returning_dict["image_url"]  = "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"
            returning_dict["first_name"] = first_name
            returning_dict["last_name"]  = last_name
            return deepcopy(returning_dict)
        return "https://www.pngmart.com/files/23/Mario-Coin-PNG-Clipart.png"
    

    # Manager
    if item in NAME_TO_MANAGER_USERNAME:
        if dictionary:
            returning_dict["image_url"] = get_current_manager_image_url(item, cache, image_urls_cache)
            return deepcopy(returning_dict)
        return get_current_manager_image_url(item, cache, image_urls_cache)
    
    # Player
    if item in players_cache:
        player_id = players_cache[item]["player_id"]
        first_name = player_ids[player_id]['first_name']
        last_name = player_ids[player_id]['last_name']
        if player_id.isnumeric():
            url = f"https://sleepercdn.com/content/nfl/players/{player_id}.jpg"
            if dictionary:
                returning_dict["image_url"] = url
                returning_dict["first_name"] = first_name
                returning_dict["last_name"]  = last_name
                return deepcopy(returning_dict)
            return url
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
    Update players cache with matchup data.
    
    Args:
        item: Either matchup data list or player_id string
        players_cache: Existing player cache (will be modified)
        player_ids: Player ID mapping
    
    Returns:
        Updated players_cache
    """
    if not item:
            raise ValueError("Item to update players cache cannot be None or empty.")
        
    if isinstance(item, str):
        player_name = player_ids.get(item, {}).get("full_name", "")

        if player_name not in players_cache:
            player_meta = player_ids.get(item, {})
            
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

    elif isinstance(item, list):
        for matchup in item:
            for player_id in matchup['players']:
                player_meta = player_ids.get(player_id, {})

                player_meta = deepcopy(player_meta)
                player_meta["player_id"] = player_id

                if player_meta.get("full_name") not in players_cache:
                    
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