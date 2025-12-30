"""
Player IDs loader and refresher for the Patriot Center backend.

Responsibilities:
- Read a cached player_ids.json file with selected player metadata fields.
- Refresh data from the Sleeper API if the cache is older than one week.
- Ensure all NFL team defenses are present as synthetic "players" with position DEF.
- Persist refreshed data back to disk in a stable, readable format.

Notes:
- This module performs file I/O and may perform network requests to Sleeper.
- Cache freshness is determined by file modification time (not a timestamp field).
- Only a subset of fields specified in FIELDS_TO_KEEP is retained from the API.
- Returned structure contains player/team entries (no metadata fields).
"""

import json
from datetime import datetime, timedelta
import os

from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.constants import *

# Fields to keep from Sleeper's player payload; reduces storage and surface area
FIELDS_TO_KEEP = [
    "full_name", "first_name", "last_name", "age", "years_exp", "college", "team",
    "depth_chart_position", "fantasy_positions", "position", "number"
]


def load_player_ids():
    """
    Load player metadata cache, refreshing if stale.

    Wrapper around update_player_ids() for external callers.
    """
    try:
        with open(PLAYER_IDS_CACHE_FILE, "r") as file:
            data = json.load(file)
    except:
        raise RuntimeError("Player IDS cache does not exist or is currupted. Investigate why.")
    
    if not data:
        raise RuntimeError("Player IDs cache is empty; please run update_player_ids() first.")
    
    return data

def update_player_ids():
    """
    Load player metadata (cached) or refresh if >7 days stale.

    Uses file modification time instead of embedded timestamp to determine freshness.
    This allows git commits to track version history without metadata fields in the JSON.

    Ensures:
        - Synthetic DEF entries present for all teams.
        - Only whitelisted fields retained.
        - Expensive Sleeper API only called if cache is >1 week old.
    """
    # Fast path: existing cache present
    data = {}
    if os.path.exists(PLAYER_IDS_CACHE_FILE):
        try:
            with open(PLAYER_IDS_CACHE_FILE, "r") as file:
                data = json.load(file)
            
            # Check file modification time to determine if cache is stale
            file_mtime = os.path.getmtime(PLAYER_IDS_CACHE_FILE)
            file_age = datetime.now() - datetime.fromtimestamp(file_mtime)

            # If file was modified within the last week, reuse it
            if file_age < timedelta(weeks=1):

                # Ensure defense entries always present even on reuse
                for team_code, team_names in TEAM_DEFENSE_NAMES.items():
                    if team_code not in data or data[team_code].get("position") != "DEF":
                        data[team_code] = {
                            "full_name": team_names["full_name"],
                            "first_name": team_names["first_name"],
                            "last_name": team_names["last_name"],
                            "team": team_code,
                            "position": "DEF"
                        }
                
                return data

            # File exists but is stale (>1 week old) - trigger refresh

        except (json.JSONDecodeError, OSError):
            # File exists but is empty, corrupted, or unreadable - trigger refresh
            pass

    # Slow path: stale or missing -> rebuild from expensive API
    new_data = fetch_updated_player_ids()

    # If players change their names they need to be changed throughout every cache file.
    _update_new_names(data, new_data)

    # Ensure all team defenses exist (avoid overwriting if already inserted)
    for team_id, team_names in TEAM_DEFENSE_NAMES.items():
        new_data.setdefault(team_id, {
            "full_name": team_names["full_name"],
            "first_name": team_names["first_name"],
            "last_name": team_names["last_name"],
            "team": team_id,
            "position": "DEF"
        })
    
    _update_players_cache(new_data)

    with open(PLAYER_IDS_CACHE_FILE, "w") as file:
        json.dump(new_data, file, indent=4)

    return new_data

def fetch_updated_player_ids():
    """
    Refresh player metadata from Sleeper players/nfl endpoint.

    Skips:
        - Defense payload originals (synthetic entries override).
    """
    response, status_code = fetch_sleeper_data("players/nfl")
    if status_code != 200:
        raise Exception("Failed to fetch player data from Sleeper API")

    filtered_data = {}
    for player_id, player_info in response.items():
        # Insert synthetic team defense entries early; skip original payload
        if player_id in TEAM_DEFENSE_NAMES:
            filtered_data[player_id] = {
                "full_name": TEAM_DEFENSE_NAMES[player_id]["full_name"],
                "first_name": TEAM_DEFENSE_NAMES[player_id]["first_name"],
                "last_name": TEAM_DEFENSE_NAMES[player_id]["last_name"],
                "team": player_id,
                "position": "DEF"
            }
            continue

        # Select only desired fields (presence-checked)
        filtered_data[player_id] = {
            key: player_info[key] for key in FIELDS_TO_KEEP if key in player_info
        }

    # (Defense entries already ensured above)
    return filtered_data


def _update_players_cache(updated_player_ids_data):
    """
    Internal utility to force-refresh player_ids.json cache.

    Primarily for development/testing; not called in normal operation.
    """
    import copy

    # Ensure all team defenses exist
    with open(PLAYERS_CACHE_FILE, "r") as file:
        players_cache = json.load(file)

    players_cache_copy = copy.deepcopy(players_cache)
    
    for player_dict in players_cache_copy.values():
        player = player_dict["full_name"]
        player_id = players_cache_copy[player]["player_id"]
        player_meta = updated_player_ids_data.get(player_id, {})

        # In case players change their name, remove the old entry
        if player_meta["full_name"] not in players_cache:
            players_cache.pop(player)

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



    with open(PLAYERS_CACHE_FILE, "w") as file:
        json.dump(players_cache, file, indent=4)
    

def _update_new_names(old_ids, new_ids):
    
    for id in new_ids:
        
        # New player entirely being added, continue
        if id not in old_ids:
            continue
        
        # player did not change their name, continue
        if old_ids[id]['full_name'] == new_ids[id]['full_name']:
            continue

        print(f"New Player Name Found:")
        print(f"     '{old_ids[id]['full_name']}' has changed his name to '{new_ids[id]['full_name']}'")

        old_player = old_ids[id]
        new_player = new_ids[id]

        cache_files = [
            MANAGER_METADATA_CACHE_FILE,
            PLAYERS_DATA_CACHE_FILE,
          # PLAYER_IDS_CACHE_FILE,         Omitted: File we are editing after this method is called.
          # PLAYERS_CACHE_FILE,            Omitted: File we are editing after this method is called.
          # REPLACEMENT_SCORE_CACHE_FILE,  Omitted: Player names are not saved in this file.
            STARTERS_CACHE_FILE,
            TRANSACTION_IDS_FILE,
            VALID_OPTIONS_CACHE_FILE
        ]
        
        for cache_file in cache_files:
            if os.path.exists(cache_file):
                with open(cache_file, "r") as file:
                    old_cache = json.load(file)
                
                new_cache = _recursive_replace(old_cache, old_player['full_name'], new_player['full_name'])
                
                with open(cache_file, "w") as file:
                    json.dump(new_cache, file, indent=4)
            

        
def _recursive_replace(data, old_str, new_str):
    """
    Recursively finds and replaces all occurrences of a string in dictionary 
    keys, dictionary values, and list elements.
    """
    if isinstance(data, str):
        # Replace string in values/elements
        return data.replace(old_str, new_str)
    elif isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # Replace string in keys, then recurse on values
            new_key = k.replace(old_str, new_str)
            new_dict[new_key] = _recursive_replace(v, old_str, new_str)
        return new_dict
    elif isinstance(data, list):
        # Recurse on list elements
        return [_recursive_replace(item, old_str, new_str) for item in data]
    else:
        # Return other types (int, float, bool, etc.) as is
        return data



player_ids = load_player_ids()
_update_players_cache(player_ids)