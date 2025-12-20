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
from patriot_center_backend.constants import TEAM_DEFENSE_NAMES, PLAYER_IDS_CACHE_FILE

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
    with open(PLAYER_IDS_CACHE_FILE, "r") as file:
        data = json.load(file)
    
    if not data:
        raise Exception("Player IDs cache is empty; please run update_player_ids() first.")
    
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
    if os.path.exists(PLAYER_IDS_CACHE_FILE):
        try:
            # Check file modification time to determine if cache is stale
            file_mtime = os.path.getmtime(PLAYER_IDS_CACHE_FILE)
            file_age = datetime.now() - datetime.fromtimestamp(file_mtime)

            # If file was modified within the last week, reuse it
            if file_age < timedelta(weeks=1):
                with open(PLAYER_IDS_CACHE_FILE, "r") as file:
                    data = json.load(file)

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

    # Ensure all team defenses exist (avoid overwriting if already inserted)
    for team_id, team_names in TEAM_DEFENSE_NAMES.items():
        new_data.setdefault(team_id, {
            "full_name": team_names["full_name"],
            "first_name": team_names["first_name"],
            "last_name": team_names["last_name"],
            "team": team_id,
            "position": "DEF"
        })

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