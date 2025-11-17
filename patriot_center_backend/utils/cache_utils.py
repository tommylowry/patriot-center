import os
import json
from datetime import datetime
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.constants import LEAGUE_IDS


def load_cache(file_path):
    """
    Load data from a JSON cache file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: The loaded data, or an empty dictionary if the file doesn't exist.
    """
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    else:
        # Initialize the cache with all years
        cache = {"Last_Updated_Season": "0", "Last_Updated_Week": 0}
        
        years = list(LEAGUE_IDS.keys())
        
        if "replacement_score" in file_path:
            first_year = min(years)
            years.extend([first_year - 3, first_year - 2, first_year - 1])
            years = sorted(years)


        for year in years:
            cache[str(year)] = {}
        return cache
    return {}


def save_cache(file_path, data):
    """
    Save data to a JSON cache file.

    Args:
        file_path (str): Path to the JSON file.
        data (dict): The data to save.
    """
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

def get_current_season_and_week():
    """
    Fetch the current season and week from the Sleeper API.

    Returns:
        tuple: The current season (int) and the current week (int).
    """
    current_year = datetime.now().year
    league_id = LEAGUE_IDS.get(int(current_year))  # Get the league ID for the current year
    if not league_id:
        raise Exception(f"No league ID found for the current year: {current_year}")
    
    # OFFLINE DEBUGGING, comment out when online
    # return "2025", 10

    sleeper_response_league = fetch_sleeper_data(f"league/{league_id}")
    if sleeper_response_league[1] != 200:
        raise Exception("Failed to fetch league data from Sleeper API")

    league_info = sleeper_response_league[0]
    current_season = int(league_info.get("season"))  # Ensure current_season is an integer
    current_week = league_info.get("settings", {}).get("last_scored_leg", 0)

    return current_season, current_week