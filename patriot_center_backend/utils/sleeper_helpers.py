"""
This module provides helper functions for interacting with the Sleeper API to retrieve and process
roster and user data for fantasy football leagues. It includes functionality to map user IDs to
roster IDs and real manager names for a given NFL season.

Functions:
    - get_roster_id: Retrieves the roster ID for a specific user from the Sleeper API response.
    - get_roster_ids: Builds a mapping of roster IDs to real manager names for a given season.

Constants:
    - LEAGUE_IDS: A dictionary mapping NFL seasons to Sleeper league IDs.
    - USERNAME_TO_REAL_NAME: A dictionary mapping Sleeper display names to real manager names.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

from patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME

SLEEPER_API_URL = "https://api.sleeper.app/v1"


def fetch_sleeper_data(endpoint: str) -> Dict[str, Any]:
    """
    Perform GET request to Sleeper API and return parsed JSON.

    Args:
        endpoint (str): Relative endpoint appended to base URL.

    Returns:
        (payload, status_code):
            payload -> dict/list on success, {"error": str} on failure.
            status_code -> 200 on success else 500.

    Notes:
        - Caller handles non-200 cases (no exceptions raised here).
        - Timeout/backoff not implemented (simple thin client).
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
    Retrieve the roster ID for a specific user from the Sleeper API response.

    Args:
        user_id (str): The user ID to find the roster ID for.
        sleeper_rosters_response (list): List of roster data from the Sleeper API.
        year

    Returns:
        int: The roster ID associated with the given user ID, or None if not found.

    Notes:
        - Special case: If owner_id is None, defaults to "Davey" for 2024 (known historical fact).
        - Roster IDs are integers from the Sleeper API.
    """
    for user in sleeper_rosters_response:
        if user['owner_id'] == user_id:
            return user['roster_id']
    
    if year == 2024:
        return "Davey"
    
    return None

def get_roster_ids(year: int) -> Dict[int, str]:
    """
    Build a mapping of roster IDs to real manager names for a given season.

    This function performs a two-step API query:
    1. Fetches all users in the league to map user_id -> real name
    2. Fetches all rosters to map roster_id -> user_id

    Then combines them to create roster_id -> real_name mapping.

    Args:
        year (int): The NFL season year.

    Returns:
        dict: Mapping of roster IDs to manager real names.
            Example: {1: "Tommy", 2: "Mike", 3: "James"}

    Notes:
        - Uses USERNAME_TO_REAL_NAME constant to convert display names to real names.
        - Roster IDs are integers from the Sleeper API.
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