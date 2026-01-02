"""
Cache utilities for the Patriot Center backend.

Responsibilities:
- Initialize/load JSON cache files with update metadata.
- Persist cache files.
- Query Sleeper API for current season/week.

Design:
- load_cache builds baseline structure when file absent (adds historical years
  for replacement_score caches to support rolling averages).
- get_current_season_and_week performs a single API call (league metadata).

All functions return plain dicts or tuples for easy JSON serialization.
"""

import os
import json
from datetime import datetime
from pathlib import Path

from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.constants import LEAGUE_IDS, PLAYERS_CACHE_FILE


def load_cache(file_path, initialize_with_last_updated_info=True):
    """
    Load JSON cache or initialize baseline structure.

    Adds:
        - Historical prior 3 seasons for replacement_score caches (rolling averages).

    Default structure:
        {
          "Last_Updated_Season": "0",
          "Last_Updated_Week": 0,
          "<year>": {}
          ...
        }

    Special case:
        If "replacement_score" in file_path, prepend 3 historical seasons
        before the earliest LEAGUE_IDS year for multi-year computations.

    Returns:
        dict: Existing or initialized cache.
    """
    if os.path.exists(file_path):
        # Load and return existing cache content
        with open(file_path, "r") as file:
            return json.load(file)
    if initialize_with_last_updated_info:
        # Initialize the cache with all years (plus historical years for replacement score caches)
        cache = {"Last_Updated_Season": "0", "Last_Updated_Week": 0}
        
        # Seed cache keys for all configured seasons
        years = list(LEAGUE_IDS.keys())
        
        # For replacement score caches, backfill extra seasons to compute multi-year averages
        if "replacement_score" in file_path:
            # Extend years list with prior 3 years (supports 3yr average calc)
            first_year = min(years)
            years.extend([first_year - 3, first_year - 2, first_year - 1])
            years = sorted(years)

        # Initialize an empty dict for each season
        for year in years:
            cache[str(year)] = {}
        return cache
    
    # For player caches, simply return an empty dict if file absent
    return {}


def save_cache(file_path, data, remove_refresh_keys=False):
    """
    Persist cache to disk using pretty formatting.

    Args:
        file_path (str): Target path.
        data (dict): Cache content.
    """
    # Persist cache atomically by writing the entire structure with 4-space indentation
    
    # Optionally remove refresh metadata before saving
    if remove_refresh_keys:
        for d in data:
            data[d].pop("refreshed", None)

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def get_current_season_and_week():
    """
    Resolve current season + last scored week from Sleeper.

    Raises:
        Exception: if active league ID not configured or API fetch fails.

    Logic:
    - Current calendar year -> league ID lookup.
    - Fetch league settings -> season + last_scored_leg.
    - last_scored_leg represents final completed scoring period.

    Returns:
        (int, int): (season, week)
    """
    current_year = datetime.now().year

    if current_year not in LEAGUE_IDS.get(int(current_year)) and datetime.now().month < 8:
        if current_year - 1 in LEAGUE_IDS.get(int(current_year)):
            current_year -= 1
        else:
            raise Exception(f"No league ID found for the current year OR the previous year: {current_year}, {current_year-1}")

    league_id = LEAGUE_IDS.get(int(current_year))  # Get the league ID for the current year
    
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
    current_week = league_info.get("settings", {}).get("last_scored_leg", 0)  # Latest scored week (0 if preseason)

    return current_season, current_week

def slug_to_player_name(slug: str) -> str:
    """Convert a slug string to a player name.

    Args:
        slug (str): The slug string (e.g., "john%20doe").

    Returns:
        str: The player name (e.g., "John Doe").
    """
    if not slug:
        return slug
    players_cache = load_cache(PLAYERS_CACHE_FILE, initialize_with_last_updated_info=False)
    if "%20" in slug or " " in slug:
        # ensure consistent encoding for lookup
        slug = slug.replace(" ", "%20").replace("'", "%27").lower()
        for p in players_cache:
            if players_cache[p]["slug"] == slug:
                return p
    
    return slug  # Fallback to returning the original string if no match found