"""
This module provides utility functions for interacting with the Sleeper API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

from patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME

SLEEPER_API_URL = "https://api.sleeper.app/v1"


def fetch_sleeper_data(endpoint: str) -> Dict[str, Any]:
    """
    Fetch data from the Sleeper API.

    Args:
        endpoint (str): The API endpoint to fetch data from.

    Returns:
        dict: Parsed JSON response from the API.

    Raises:
        ConnectionAbortedError: If the API call fails.
    """
    # Construct full URL from configured base and endpoint
    url = f"{SLEEPER_API_URL}/{endpoint}"

    response = requests.get(url)
    
    if response.status_code != 200:
        raise ConnectionAbortedError(f"Failed to fetch data from Sleeper API with call to {url}")

    # Return parsed JSON 
    return response.json()

def get_roster_id(user_id: str, year: int, sleeper_rosters_response: Optional[List[Dict[str, Any]]]) -> (str | None):
    """
    Get the roster ID for a given user ID.

    Args:
        user_id (str): The Sleeper user ID.
        year (int): The NFL season year.

    Returns:
        str | None: The roster ID for the user, or None if not found.
    """
    for user in sleeper_rosters_response:
        if user['owner_id'] == user_id:
            return user['roster_id']
    
    if year == 2024:
        return "Davey"
    
    return None

def get_roster_ids(year: int) -> Dict[int, str]:
    """
    Get a dictionary mapping roster IDs to user names.

    Args:
        year (int): The NFL season year.

    Returns:
        dict: A dictionary mapping roster IDs to user names.
    """
    user_ids = {}
    sleeper_users_response = fetch_sleeper_data(f"league/{LEAGUE_IDS[year]}/users")
    for user in sleeper_users_response:
        user_ids[user['user_id']] = USERNAME_TO_REAL_NAME[user['display_name']]
    
    roster_ids = {}
    sleeper_rosters_response = fetch_sleeper_data(f"league/{LEAGUE_IDS[year]}/rosters")
    for user in sleeper_rosters_response:
        
        roster_ids[user['roster_id']] = get_roster_id(user['owner_id'], year,
                                                      sleeper_rosters_response=sleeper_rosters_response)

    return roster_ids

def get_current_season_and_week() -> Tuple[int, int]:
    """
    Get the current NFL season and week.

    Returns:
        Tuple[int, int]: A tuple containing the current season and week.
    """
    current_year = datetime.now().year

    if current_year not in LEAGUE_IDS and datetime.now().month < 8:
        if current_year - 1 in LEAGUE_IDS:
            current_year -= 1
        else:
            raise Exception(f"No league ID found for the current year OR the previous year: {current_year}, {current_year-1}")

    league_id = LEAGUE_IDS.get(int(current_year))  # Get the league ID for the current year
    
    # OFFLINE DEBUGGING, comment out when online
    # return "2025", 10

    # Query Sleeper API for league metadata
    league_info = fetch_sleeper_data(f"league/{league_id}")
    
    current_season = int(league_info.get("season"))

    # last_scored_leg is the latest completed/scored fantasy week
    current_week = int(league_info.get("settings", {}).get("last_scored_leg", 0))  # Latest scored week (0 if preseason)

    return current_season, current_week