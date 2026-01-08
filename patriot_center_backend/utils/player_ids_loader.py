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
from copy import deepcopy

from patriot_center_backend.cache import get_cache_manager
from patriot_center_backend.constants import TEAM_DEFENSE_NAMES
from patriot_center_backend.utils.helpers import fetch_sleeper_data

CACHE_MANAGER = get_cache_manager()

PLAYER_IDS_CACHE       = CACHE_MANAGER.get_player_ids_cache()
MANAGER_METADATA_CACHE = CACHE_MANAGER.get_manager_cache()
PLAYER_DATA_CACHE      = CACHE_MANAGER.get_player_data_cache()
STARTERS_CACHE         = CACHE_MANAGER.get_starters_cache()
TRANSACTION_IDS_CACHE  = CACHE_MANAGER.get_transaction_ids_cache()
VALID_OPTIONS_CACHE    = CACHE_MANAGER.get_valid_options_cache()
PLAYERS_CACHE          = CACHE_MANAGER.get_players_cache()


# Fields to keep from Sleeper's player payload; reduces storage and surface area
FIELDS_TO_KEEP = [
    "full_name", "first_name", "last_name", "age", "years_exp", "college", "team",
    "depth_chart_position", "fantasy_positions", "position", "number"
]


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
    if CACHE_MANAGER.is_player_ids_cache_stale():

        response = fetch_sleeper_data("players/nfl")

        old_data = deepcopy(PLAYER_IDS_CACHE)

        for player_id, player_info in response.items():
            # Insert synthetic team defense entries early; skip original payload
            if player_id in TEAM_DEFENSE_NAMES:
                PLAYER_IDS_CACHE[player_id] = {
                    "full_name": TEAM_DEFENSE_NAMES[player_id]["full_name"],
                    "first_name": TEAM_DEFENSE_NAMES[player_id]["first_name"],
                    "last_name": TEAM_DEFENSE_NAMES[player_id]["last_name"],
                    "team": player_id,
                    "position": "DEF"
                }
                continue



            # Select only desired fields (presence-checked)
            PLAYER_IDS_CACHE[player_id] = {
                key: player_info[key] for key in FIELDS_TO_KEEP if key in player_info
            }
        
        # Fill in missing defenses that don't exist anymore (OAK, etc.)
        for player_id in TEAM_DEFENSE_NAMES:
            if player_id not in PLAYER_IDS_CACHE:
                PLAYER_IDS_CACHE[player_id] = {
                    "full_name": TEAM_DEFENSE_NAMES[player_id]["full_name"],
                    "first_name": TEAM_DEFENSE_NAMES[player_id]["first_name"],
                    "last_name": TEAM_DEFENSE_NAMES[player_id]["last_name"],
                    "team": player_id,
                    "position": "DEF"
                }
        

        # If players change their names they need to be changed throughout every cache file.
        _update_new_names(old_data)
        _update_players_cache()
        
        # save all the cache
        CACHE_MANAGER.save_all_caches()

def fetch_updated_player_ids():
    """
    Refresh player metadata from Sleeper players/nfl endpoint.

    Skips:
        - Defense payload originals (synthetic entries override).
    """
    response = fetch_sleeper_data("players/nfl")

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

def _update_players_cache():
    """
    Internal utility to force-refresh player_ids.json cache.

    Primarily for development/testing; not called in normal operation.
    """
    players_cache_copy = deepcopy(PLAYERS_CACHE)
    
    for player_dict in players_cache_copy.values():
        player = player_dict["full_name"]
        player_id = players_cache_copy[player]["player_id"]
        player_meta = deepcopy(PLAYER_IDS_CACHE.get(player_id, {}))

        # In case players change their name, remove the old entry
        if player_meta["full_name"] not in PLAYERS_CACHE:
            PLAYERS_CACHE.pop(player)

        slug = player_meta.get("full_name", "").lower()
        slug = slug.replace(" ", "%20")
        slug = slug.replace("'", "%27")
        PLAYERS_CACHE[player_meta["full_name"]] = {
            "full_name": player_meta.get("full_name", ""),
            "first_name": player_meta.get("first_name", ""),
            "last_name": player_meta.get("last_name", ""),
            "position": player_meta.get("position", ""),
            "team": player_meta.get("team", ""),
            "slug": slug,
            "player_id": player_id
        }
    
def _update_new_names(old_ids):
    
    for id in PLAYER_IDS_CACHE:
        
        # New player entirely being added, continue
        if id not in old_ids:
            continue
        
        # player did not change their name, continue
        if old_ids[id]['full_name'] == PLAYER_IDS_CACHE[id]['full_name']:
            continue

        print(f"New Player Name Found:")
        print(f"     '{old_ids[id]['full_name']}' has changed his name to '{PLAYER_IDS_CACHE[id]['full_name']}'")

        old_player = old_ids[id]
        new_player = PLAYER_IDS_CACHE[id]

        MANAGER_METADATA_CACHE = _recursive_replace(MANAGER_METADATA_CACHE, old_player['full_name'], new_player['full_name'])
        PLAYER_DATA_CACHE      = _recursive_replace(PLAYER_DATA_CACHE,      old_player['full_name'], new_player['full_name'])
        STARTERS_CACHE         = _recursive_replace(STARTERS_CACHE,         old_player['full_name'], new_player['full_name'])
        TRANSACTION_IDS_CACHE  = _recursive_replace(TRANSACTION_IDS_CACHE,  old_player['full_name'], new_player['full_name'])
        VALID_OPTIONS_CACHE    = _recursive_replace(VALID_OPTIONS_CACHE,    old_player['full_name'], new_player['full_name'])

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