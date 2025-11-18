"""
Cache utilities for the Patriot Center backend.

Responsibilities:
- Load a JSON cache file (creating a structured default cache if missing).
- Save a JSON cache file with pretty formatting.
- Query Sleeper API to determine the current season and week.

Notes:
- When a cache file does not exist, an initial structure is created with
  Last_Updated_Season/Week markers and a per-season dictionary seeded from
  LEAGUE_IDS. For "replacement_score" caches, additional prior seasons are
  included to support multi-year averages.
- External network calls are performed in get_current_season_and_week via the Sleeper API.
"""

import os
import json
from datetime import datetime
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.constants import LEAGUE_IDS


def load_cache(file_path):
    """
    Load data from a JSON cache file, or initialize a new cache structure.

    Behavior:
    - If file exists, returns its JSON content.
    - If missing, returns a dict pre-seeded with:
      - Last_Updated_Season: "0"
      - Last_Updated_Week: 0
      - One empty dict per season from LEAGUE_IDS.
      - Special case: if "replacement_score" appears in file_path, includes
        three additional seasons prior to the earliest LEAGUE_IDS year to
        support multi-year computations (e.g., 3-year rolling averages).

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: The loaded data, or an initialized cache structure if the file doesn't exist.
    """
    if os.path.exists(file_path):
        # Load and return existing cache content
        with open(file_path, "r") as file:
            return json.load(file)
    else:
        # Initialize the cache with all years (plus historical years for replacement score caches)
        cache = {"Last_Updated_Season": "0", "Last_Updated_Week": 0}
        
        # Seed cache keys for all configured seasons
        years = list(LEAGUE_IDS.keys())
        
        # For replacement score caches, backfill extra seasons to compute multi-year averages
        if "replacement_score" in file_path:
            first_year = min(years)
            years.extend([first_year - 3, first_year - 2, first_year - 1])
            years = sorted(years)

        # Initialize an empty dict for each season
        for year in years:
            cache[str(year)] = {}
        return cache
    # Fallback (should be unreachable because function returns above)
    return {}


def save_cache(file_path, data):
    """
    Save data to a JSON cache file with indentation for readability.

    Args:
        file_path (str): Path to the JSON file.
        data (dict): The data to save.
    """
    # Persist cache atomically by writing the entire structure with 4-space indentation
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def get_current_season_and_week():
    """
    Fetch the current season and week from the Sleeper API.

    Behavior:
    - Resolves the league ID from LEAGUE_IDS using the current calendar year.
    - Calls Sleeper's league endpoint to obtain season and last scored week.
    - Returns both as integers.

    Raises:
        Exception: If a league ID is not found for the current year, or if the
        Sleeper API call fails.

    Returns:
        tuple: The current season (int) and the current week (int).
    """
    current_year = datetime.now().year
    # Look up the active league ID for the calendar year; required for API call
    league_id = LEAGUE_IDS.get(int(current_year))  # Get the league ID for the current year
    if not league_id:
        raise Exception(f"No league ID found for the current year: {current_year}")
    
    # OFFLINE DEBUGGING, comment out when online
    # return "2025", 10

    # Query Sleeper API for league metadata
    sleeper_response_league = fetch_sleeper_data(f"league/{league_id}")
    if sleeper_response_league[1] != 200:
        # Surface a clear error if the upstream request fails
        raise Exception("Failed to fetch league data from Sleeper API")

    league_info = sleeper_response_league[0]
    # Ensure current_season is an integer for downstream numeric comparisons
    current_season = int(league_info.get("season"))  # Ensure current_season is an integer
    # last_scored_leg is the latest completed/scored fantasy week
    current_week = league_info.get("settings", {}).get("last_scored_leg", 0)

    return current_season, current_week