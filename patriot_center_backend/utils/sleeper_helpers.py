"""
This module provides utility functions for interacting with the Sleeper API.
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple

import requests

from patriot_center_backend.constants import (
    LEAGUE_IDS,
    USERNAME_TO_REAL_NAME,
)

SLEEPER_API_URL = "https://api.sleeper.app/v1"


def fetch_sleeper_data(endpoint: str) -> Dict[str, Any]:
    """
    Fetches data from the Sleeper API given an endpoint.

    Args:
        endpoint: The endpoint to call on the Sleeper API.

    Returns:
        The parsed JSON response from the Sleeper API.

    Raises:
        ConnectionAbortedError: If the request to the Sleeper API fails.
    """
    url = f"{SLEEPER_API_URL}/{endpoint}"

    response = requests.get(url)
    
    if response.status_code != 200:
        raise ConnectionAbortedError(f"Failed to fetch data from Sleeper API with call to {url}")

    # Return parsed JSON 
    return response.json()

def get_roster_id(user_id: str, year: int, sleeper_rosters_response: List[Dict[str, Any]] = None) -> int | None:
    """
    Retrieves a roster ID for a given user ID and year.

    Args:
        user_id (str): The user ID to retrieve the roster ID for.
        year (int): The year to retrieve the roster ID for.
        sleeper_rosters_response (List[Dict[str, Any]], optional): The response from the Sleeper API
            containing the rosters data. If not provided, the function will fetch the data itself.

    Returns:
        int | None: The roster ID for the given user ID, or None if the user ID is not found.
    """
    if sleeper_rosters_response is None:
        sleeper_rosters_response = fetch_sleeper_data(f"league/{LEAGUE_IDS[year]}/rosters")

    # Iterate over the rosters data and find the roster ID for the given user ID
    for user in sleeper_rosters_response:
        if user['owner_id'] == user_id:
            return user['roster_id']
    
    return None

def get_roster_ids(year: int) -> Dict[int, str]:
    """
    Retrieves a mapping of roster IDs to real names for a given year.

    Args:
        year (int): The year for which to retrieve the roster IDs.

    Returns:
        dict: Mapping of roster IDs to real names.

    Raises:
        Exception: If not all roster IDs are assigned to a user.
    """
    user_ids = {}

    # Fetch the users data from the Sleeper API
    sleeper_users_response = fetch_sleeper_data(f"league/{LEAGUE_IDS[year]}/users")

    # Iterate over the users data and store the user IDs with their real names
    for user in sleeper_users_response:
        user_ids[user['user_id']] = USERNAME_TO_REAL_NAME[user['display_name']]

    roster_ids = {}

    # Fetch the rosters data from the Sleeper API
    sleeper_rosters_response = fetch_sleeper_data(f"league/{LEAGUE_IDS[year]}/rosters")

    # Iterate over the rosters data and store the roster IDs
    users_missing = []
    for user in sleeper_rosters_response:
        user_id   = user['owner_id']
        roster_id = get_roster_id(user_id, year, sleeper_rosters_response=sleeper_rosters_response)
        
        if not roster_id:
            users_missing.append(user_ids[user_id])
            continue

        # Store the roster ID and the real name of the user
        roster_ids[roster_id] = user_ids[user_id]


    # In 2024 special case, if there is only one user missing, assign them the roster_id missing from the roster_ids
    if year == 2024 and len(users_missing) == 1:
        for i in range(1, len(user_ids) + 1):
            if i not in roster_ids:
                roster_ids[i] = users_missing[0]
    

    # If not all roster_ids are assigned to a user, raise an error
    if len(roster_ids) != len(user_ids):
        raise Exception(f"Missing rosters for the following users: {users_missing}")
    
    return roster_ids

def get_current_season_and_week() -> Tuple[int, int]:
    """
    Retrieves the current season and week number based on the current date.

    The current season is determined by the year. If the current year is not in the LEAGUE_IDS,
    and the current month is less than 8, the previous year is used.
    Otherwise, the current year is used.

    The current week number is determined by the latest completed/scored fantasy week.
    If the current week is in the preseason, the week number is 0.

    Returns:
        tuple: (current_season, current_week)
    """
    current_year = datetime.now().year

    if current_year > max(LEAGUE_IDS.keys()):
        current_year = max(LEAGUE_IDS.keys())

    league_id = LEAGUE_IDS.get(int(current_year))
    
    # # OFFLINE DEBUGGING
    # return "2025", 10

    # Query Sleeper API for league metadata
    league_info = fetch_sleeper_data(f"league/{league_id}")
    
    current_season = int(league_info.get("season"))

    # last_scored_leg is the latest completed/scored fantasy week
    current_week = int(league_info.get("settings", {}).get("last_scored_leg", 0))  # Latest scored week (0 if preseason)

    return current_season, current_week