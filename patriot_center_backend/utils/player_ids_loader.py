"""
Player IDs loader and refresher for the Patriot Center backend.

Responsibilities:
- Read a cached player_ids.json file with selected player metadata fields.
- Refresh data from the Sleeper API if the cache is older than one week.
- Ensure all NFL team defenses are present as synthetic "players" with position DEF.
- Persist refreshed data back to disk in a stable, readable format.

Notes:
- This module performs file I/O and may perform network requests to Sleeper.
- The cache is timestamped with a Last_Updated YYYY-MM-DD string.
- Only a subset of fields specified in FIELDS_TO_KEEP is retained from the API.
"""

import json
from datetime import datetime, timedelta
import os
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data

# Path to the player_ids.json file in the data directory
PLAYER_IDS_FILE = "patriot_center_backend/data/player_ids.json"

# Fields to keep from Sleeper's player payload; reduces storage and surface area
FIELDS_TO_KEEP = [
    "full_name", "age", "years_exp", "college", "team",
    "depth_chart_position", "fantasy_positions", "position", "number"
]

# Mapping of team IDs to their full names
# Used to synthesize "DEF" entries for each NFL team defense
TEAM_DEFENSE_NAMES = {
    "SEA": "Seattle Seahawks",
    "CHI": "Chicago Bears",
    "NE": "New England Patriots",
    "DAL": "Dallas Cowboys",
    "GB": "Green Bay Packers",
    "KC": "Kansas City Chiefs",
    "SF": "San Francisco 49ers",
    "PIT": "Pittsburgh Steelers",
    "PHI": "Philadelphia Eagles",
    "BUF": "Buffalo Bills",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "DEN": "Denver Broncos",
    "CLE": "Cleveland Browns",
    "CIN": "Cincinnati Bengals",
    "BAL": "Baltimore Ravens",
    "LAR": "Los Angeles Rams",
    "LAC": "Los Angeles Chargers",
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "CAR": "Carolina Panthers",
    "DET": "Detroit Lions",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "LV": "Las Vegas Raiders",
    "NO": "New Orleans Saints",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders"
}

def load_player_ids():
    """
    Load player metadata from the local cache, refreshing from Sleeper if stale.

    Behavior:
    - If PLAYER_IDS_FILE exists and is newer than one week (based on Last_Updated),
      load it and ensure all team defenses are present as DEF entries.
    - Otherwise, fetch fresh data from Sleeper, filter the fields, add defenses,
      stamp Last_Updated, and persist to PLAYER_IDS_FILE.

    Side effects:
    - May perform network I/O via fetch_sleeper_data.
    - Performs file reads/writes to PLAYER_IDS_FILE.

    Returns:
    - dict: Mapping of player_id (or team code for defenses) to a dict of metadata.

    Raises:
    - Exception: Propagates if Sleeper API fetch fails in refresh path.
    """
    # Check if the file exists
    if os.path.exists(PLAYER_IDS_FILE):
        with open(PLAYER_IDS_FILE, "r") as file:
            data = json.load(file)
        
        # Determine whether the cache is still fresh (within 1 week)
        last_updated = datetime.strptime(data.get("Last_Updated", "1970-01-01"), "%Y-%m-%d")
        if datetime.now() - last_updated < timedelta(weeks=1):
            # Ensure team defenses are included in the data even if file is fresh
            for player_id, player_info in data.items():
                # If the key matches a team code, populate a DEF entry
                if player_id in TEAM_DEFENSE_NAMES:
                    data[player_id] = {
                        "full_name": TEAM_DEFENSE_NAMES[player_id],
                        "team": player_id,
                        "position": "DEF"  # Set position as "DEF" for team defenses
                    }
                    continue
            return data  # Return the updated data
    
    # If the file is outdated or doesn't exist, fetch new data from Sleeper
    new_data = fetch_updated_player_ids()
    new_data["Last_Updated"] = datetime.now().strftime("%Y-%m-%d")
    
    # Ensure team defenses are included in the new data (idempotent insert)
    for team_id, team_name in TEAM_DEFENSE_NAMES.items():
        if team_id not in new_data:
            new_data[team_id] = {
                "full_name": team_name,
                "team": team_id,
                "position": "DEF"
            }
    
    # Save the updated data to the file with pretty formatting
    with open(PLAYER_IDS_FILE, "w") as file:
        json.dump(new_data, file, indent=4)
    
    return new_data

def fetch_updated_player_ids():
    """
    Fetch and filter player metadata from the Sleeper API.

    Behavior:
    - Calls Sleeper endpoint "players/nfl".
    - On success, returns a dict filtered to FIELDS_TO_KEEP for players.
    - Inserts synthetic DEF entries for every NFL team specified in TEAM_DEFENSE_NAMES.

    Returns:
    - dict: Mapping of player_id (or team code for defenses) to selected metadata fields.

    Raises:
    - Exception: If the Sleeper API call returns a non-200 status code.
    """
    response, status_code = fetch_sleeper_data("players/nfl")
    if status_code != 200:
        # Bubble up a clear error to the caller when API request fails
        raise Exception("Failed to fetch player data from Sleeper API")
    
    # Filter the response to include only the desired fields
    filtered_data = {}
    for player_id, player_info in response.items():
        # Add team defenses as synthetic players with position DEF
        if player_id in TEAM_DEFENSE_NAMES:
            filtered_data[player_id] = {
                "full_name": TEAM_DEFENSE_NAMES[player_id],
                "team": player_id,
                "position": "DEF"  # Set position as "DEF" for team defenses
            }
            continue
        
        # For regular players, keep only the desired fields to minimize storage
        filtered_data[player_id] = {key: player_info[key] for key in FIELDS_TO_KEEP if key in player_info}
    
    return filtered_data