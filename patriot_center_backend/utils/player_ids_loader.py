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

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import TEAM_DEFENSE_NAMES
from patriot_center_backend.utils.helpers import fetch_sleeper_data


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
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    if CACHE_MANAGER.is_player_ids_cache_stale():

        response = fetch_sleeper_data("players/nfl")

        old_data = deepcopy(player_ids_cache)

        for player_id, player_info in response.items():
            # Insert synthetic team defense entries early; skip original payload
            if player_id in TEAM_DEFENSE_NAMES:
                player_ids_cache[player_id] = {
                    "full_name": TEAM_DEFENSE_NAMES[player_id]["full_name"],
                    "first_name": TEAM_DEFENSE_NAMES[player_id]["first_name"],
                    "last_name": TEAM_DEFENSE_NAMES[player_id]["last_name"],
                    "team": player_id,
                    "position": "DEF"
                }
                continue



            # Select only desired fields (presence-checked)
            player_ids_cache[player_id] = {
                key: player_info[key] for key in FIELDS_TO_KEEP if key in player_info
            }
        
        # Fill in missing defenses that don't exist anymore (OAK, etc.)
        for player_id in TEAM_DEFENSE_NAMES:
            if player_id not in player_ids_cache:
                player_ids_cache[player_id] = {
                    "full_name": TEAM_DEFENSE_NAMES[player_id]["full_name"],
                    "first_name": TEAM_DEFENSE_NAMES[player_id]["first_name"],
                    "last_name": TEAM_DEFENSE_NAMES[player_id]["last_name"],
                    "team": player_id,
                    "position": "DEF"
                }
        

        # If players change their names they need to be changed throughout every cache file.
        _update_new_names(old_data)
        
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
    
def _update_new_names(old_ids):
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()
    
    for id in player_ids_cache:
        
        # New player entirely being added, continue
        if id not in old_ids:
            continue
        
        # player did not change their name, continue
        if old_ids[id]['full_name'] == player_ids_cache[id]['full_name']:
            continue

        print(f"New Player Name Found:")
        print(f"     '{old_ids[id]['full_name']}' has changed his name to '{player_ids_cache[id]['full_name']}'")

        old_player = old_ids[id]
        new_player = player_ids_cache[id]

        manager_metadata_cache = CACHE_MANAGER.get_manager_cache()
        player_data_cache      = CACHE_MANAGER.get_player_data_cache()
        starters_cache         = CACHE_MANAGER.get_starters_cache()
        transaction_ids_cache  = CACHE_MANAGER.get_transaction_ids_cache()
        valid_options_cache    = CACHE_MANAGER.get_valid_options_cache()
        players_cache          = CACHE_MANAGER.get_players_cache()

        manager_metadata_cache = _recursive_replace(manager_metadata_cache, old_player['full_name'], new_player['full_name'])
        player_data_cache      = _recursive_replace(player_data_cache,      old_player['full_name'], new_player['full_name'])
        starters_cache         = _recursive_replace(starters_cache,         old_player['full_name'], new_player['full_name'])
        transaction_ids_cache  = _recursive_replace(transaction_ids_cache,  old_player['full_name'], new_player['full_name'])
        valid_options_cache    = _recursive_replace(valid_options_cache,    old_player['full_name'], new_player['full_name'])
        players_cache          = _recursive_replace(players_cache,          old_player['full_name'], new_player['full_name'])


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