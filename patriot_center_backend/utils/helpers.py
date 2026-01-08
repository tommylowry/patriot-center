from datetime import datetime
from typing import Any, Dict, Tuple

import requests

from patriot_center_backend.cache import get_cache_manager
from patriot_center_backend.constants import LEAGUE_IDS

CACHE_MANAGER = get_cache_manager()

PLAYER_IDS_CACHE = CACHE_MANAGER.get_player_ids_cache()
PLAYERS_CACHE    = CACHE_MANAGER.get_players_cache()

SLEEPER_API_URL = "https://api.sleeper.app/v1"

PLAYER_NAME_TO_ID = {
    player_info.get("full_name"): pid 
    for pid, player_info in PLAYER_IDS_CACHE.items()
}


def get_player_id(player_name: str) -> str:
    """
    Retrieve the player ID for a given player name from the player IDs cache.

    Args:
        player_name (str): The full name of the player.
        player_ids_cache (dict): A dictionary mapping player names to their IDs.

    Returns:
        str or None: The player ID if found, otherwise None.
    """
    return PLAYER_NAME_TO_ID.get(player_name)

def get_player_name(player_id: str) -> str|None:
    """
    Retrieve the player name for a given player ID from the player IDs cache.

    Args:
        player_id (str): The ID of the player.
        player_ids_cache (dict): A dictionary mapping player names to their IDs.

    Returns:
        str or None: The player name if found, otherwise None.
    """
    player_info = PLAYER_IDS_CACHE.get(player_id)
    if player_info:
        return player_info.get("full_name", None)
    return None

def slug_to_player_name(slug: str) -> str:
    """Convert a slug string to a player name.

    Args:
        slug (str): The slug string (e.g., "john%20doe").

    Returns:
        str: The player name (e.g., "John Doe").
    """
    if not slug:
        return slug
    
    if "%20" in slug or " " in slug:

        # ensure consistent encoding for lookup
        slug = slug.replace(" ", "%20").replace("'", "%27").lower()
        for p in PLAYERS_CACHE:
            if PLAYERS_CACHE[p]["slug"] == slug:
                return p
    
    return slug  # Fallback to returning the original string if no match found

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
    
    # Ensure current_season is an integer for downstream numeric comparisons
    current_season = int(league_info.get("season"))  # Ensure current_season is an integer
    # last_scored_leg is the latest completed/scored fantasy week
    current_week = int(league_info.get("settings", {}).get("last_scored_leg", 0))  # Latest scored week (0 if preseason)

    return current_season, current_week

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