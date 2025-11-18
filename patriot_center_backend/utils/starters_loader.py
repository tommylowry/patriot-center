"""Starters cache builder/updater for Patriot Center.

Responsibilities:
- Maintain per-week starters and points per manager from Sleeper.
- Incrementally update a JSON cache, resuming from Last_Updated_* markers.
- Normalize totals to 2 decimals and resolve manager display names.

Notes:
- Weeks are capped at 14 to exclude fantasy playoffs.
- Import-time execution at bottom warms the cache for downstream consumers.
"""
from decimal import Decimal
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME
from patriot_center_backend.utils.player_ids_loader import load_player_ids
from patriot_center_backend.utils.cache_utils import load_cache, save_cache, get_current_season_and_week


# Constants
# Path to starters cache; PLAYER_IDS is used to map names/positions for lineup entries.
STARTERS_CACHE_FILE = "patriot_center_backend/data/starters_cache.json"
PLAYER_IDS = load_player_ids()


def load_or_update_starters_cache():
    """
    Load starters data from the cache file. If the cache is outdated or doesn't exist,
    fetch only the missing data from the Sleeper API and update the cache.

    Behavior:
    - Loads the existing cache or initializes it if missing.
    - Detects the current season/week (capped at 14) and computes only missing weeks.
    - Uses Last_Updated_Season/Week to resume incrementally across runs.
    - Writes updates back to disk and strips metadata before returning.

    Side effects:
    - Reads/writes the starters cache JSON.
    - Calls the Sleeper API (users, rosters, matchups) as needed.

    Returns:
        dict: The updated starters cache (without Last_Updated_* metadata).
    """
    # Load existing cache or initialize a new one
    cache = load_cache(STARTERS_CACHE_FILE)

    # Dynamically determine the current season and week
    current_season, current_week = get_current_season_and_week()
    if current_week > 14:
        # Cap to regular season only for comparability across years
        current_week = 14

    
    # Process all years in LEAGUE_IDS
    for year in LEAGUE_IDS.keys():

        # Get the last updated season and week from the cache
        last_updated_season = int(cache.get("Last_Updated_Season", 0))
        last_updated_week   = cache.get("Last_Updated_Week", 0)

        # Skip past-fully-computed seasons; reset week counter when moving to a new year
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                cache['Last_Updated_Week'] = 0
        
        # Short-circuit if fully up to date for live season/week
        if last_updated_season == int(current_season) and last_updated_week == current_week:
            break

        year = int(year)  # Ensure year is an integer
        max_weeks = _get_max_weeks(year, current_season, current_week)

        # Determine the range of weeks to update
        if year == current_season or year == last_updated_season:
            # Continue from last updated week within the same/live season
            last_updated_week = cache.get("Last_Updated_Week", 0)
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            # Backfill full season when outside the last-updated season
            weeks_to_update = range(1, max_weeks + 1)

        if list(weeks_to_update) == []:
            continue
        
        print(f"Updating starters cache for season {year}, weeks: {list(weeks_to_update)}")

        # Fetch and update only the missing weeks for the year
        for week in weeks_to_update:
            if str(year) not in cache:
                cache[str(year)] = {}
            # Pull week detail from Sleeper and store per-manager lineup/points
            cache[str(year)][str(week)] = fetch_starters_for_week(year, week)

            # Advance progress markers to support resumable updates
            cache['Last_Updated_Season'] = str(year)
            cache['Last_Updated_Week'] = week

            print("  Starters cache updated internally for season {}, week {}".format(year, week))

    # Save the updated cache to the file
    save_cache(STARTERS_CACHE_FILE, cache)

    # Remove metadata before returning
    cache.pop("Last_Updated_Season", None)
    cache.pop("Last_Updated_Week", None)

    return cache


def _get_max_weeks(season, current_season, current_week):
    """
    Determine the maximum number of weeks for a given season.

    Args:
        season (int): The season to determine the max weeks for.
        current_season (int): The current season.
        current_week (int): The current week.

    Returns:
        int: The maximum number of weeks for the season.

    Notes:
    - Seasons 2019 and 2020 are capped at 13 (league rule set then).
    - All other seasons capped at 14 (regular season only).
    - For the current season, cap to the current in-progress week.
    """
    if season == current_season:
        return current_week  # Use the current week for the current season
    elif season in [2019, 2020]:
        return 13  # Cap at 13 weeks for 2019 and 2020
    else:
        return 14  # Cap at 14 weeks for other seasons


def fetch_starters_for_week(season, week):
    """
    Fetch starters data for a specific season and week.

    Behavior:
    - Resolves league users and maps display names to real names.
    - Handles special-case name/roster overrides for known seasons.
    - Retrieves starters and their half-PPR points for the week.

    Args:
        season (int): The season to fetch data for.
        week (int): The week to fetch data for.

    Returns:
        dict: The starters data for the given season and week, keyed by manager real name.
              Empty dict if users fetch fails.
    """
    league_id = LEAGUE_IDS[int(season)]
    sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
    if sleeper_response_users[1] != 200:
        return {}  # Return empty data if the API call fails

    managers = sleeper_response_users[0]
    week_data = {}
    for manager in managers:
        real_name = USERNAME_TO_REAL_NAME.get(manager['display_name'], "Unknown Manager")
        
        # Tommy started the 2019 season for 3 weeks before Cody took over
        if int(season) == 2019 and week < 4 and real_name == "Cody":
            real_name = "Tommy"
        
        roster_id = get_roster_id(season, manager['user_id'])
        if roster_id is None:
            # Handle special cases for known roster IDs
            if int(season) == 2024 and real_name == "Davey":
                roster_id = 4
        
        if not roster_id:
            continue

        # Fetch starters for the manager
        starters_data = get_starters_data(league_id, roster_id, week)
        if starters_data:
            week_data[real_name] = starters_data

    return week_data


def get_roster_id(year, user_id):
    """
    Fetch the roster ID for a specific user in a given year.

    Behavior:
    - Queries Sleeper rosters for the league and finds the one owned by user_id.

    Args:
        year (int): The year to fetch the roster ID for.
        user_id (str): The user ID to fetch the roster ID for.

    Returns:
        str: The roster ID, or None if not found or API error occurs.
    """
    league_id = LEAGUE_IDS[int(year)]
    sleeper_response_rosters = fetch_sleeper_data(f"league/{league_id}/rosters")
    if sleeper_response_rosters[1] != 200:
        return None

    rosters = sleeper_response_rosters[0]
    for roster in rosters:
        if roster['owner_id'] == user_id:
            return roster['roster_id']
    return None


def get_starters_data(league_id, roster_id, week):
    """
    Fetch starters data for a specific roster and week.

    Behavior:
    - Retrieves matchups, locates the record for roster_id, and builds:
      { player_name: {points, position}, "Total_Points": float }.
    - Filters out unknown players/positions to keep cache clean.
    - Rounds total points to two decimals via Decimal normalization.

    Args:
        league_id (str): The league ID.
        roster_id (str): The roster ID.
        week (int): The week to fetch data for.

    Returns:
        dict: The starters data for the given roster and week, or None on API error/absence.
    """
    sleeper_response_matchups = fetch_sleeper_data(f"league/{league_id}/matchups/{week}")
    if sleeper_response_matchups[1] != 200:
        return None

    matchups = sleeper_response_matchups[0]
    for matchup in matchups:
        if matchup['roster_id'] == roster_id:
            manager_data = {"Total_Points": 0}
            for player_id in matchup['starters']:
                player_name = PLAYER_IDS.get(player_id, {}).get('full_name', 'Unknown Player')
                if player_name == 'Unknown Player':
                    continue
                player_score = matchup['players_points'].get(player_id, 0)
                player_position = PLAYER_IDS.get(player_id, {}).get('position', 'Unknown Position')
                if player_position == 'Unknown Position':
                    continue

                # Add player data
                manager_data[player_name] = {
                    "points": player_score,
                    "position": player_position
                }

                # Update total points
                manager_data["Total_Points"] += player_score

            # Normalize to 2 decimals; consistent presentation across weeks/managers
            manager_data["Total_Points"] = float(Decimal(manager_data["Total_Points"]).quantize(Decimal('0.01')).normalize())

            return manager_data

    return None

# Warm the cache on import so downstream consumers can read a ready dataset.
load_or_update_starters_cache()