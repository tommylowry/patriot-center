import json
import os
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
import patriot_center_backend.constants as consts
from patriot_center_backend.utils.player_ids_loader import load_player_ids
from decimal import Decimal
from datetime import datetime

STARTERS_CACHE_FILE = "patriot_center_backend/data/starters_cache.json"
PLAYER_IDS = load_player_ids()

def load_or_update_starters_cache():
    """
    Load starters data from the cache file. If the cache is outdated or doesn't exist,
    fetch only the missing data from the Sleeper API and update the cache.
    """
    # Check if the cache file exists
    if os.path.exists(STARTERS_CACHE_FILE):
        with open(STARTERS_CACHE_FILE, "r") as file:
            cache = json.load(file)
    else:
        # Initialize the cache with all years
        cache = {"Last_Updated_Season": None, "Last_Updated_Week": 0}
        for year in consts.LEAGUE_IDS.keys():
            cache[year] = {}

    # Dynamically determine the current season and league ID
    current_year = datetime.now().year
    league_id = consts.LEAGUE_IDS.get(current_year)  # Get the league ID for the current year
    if not league_id:
        current_year = list(consts.LEAGUE_IDS.keys())[-1]  # Fallback to the latest year available
        league_id = consts.LEAGUE_IDS[current_year]

    # Fetch the current season and week from the Sleeper API
    sleeper_response_league = fetch_sleeper_data(f"league/{league_id}")
    if sleeper_response_league[1] != 200:
        raise Exception("Failed to fetch league data from Sleeper API")
    
    league_info = sleeper_response_league[0]
    current_season = int(league_info.get("season"))  # Ensure current_season is an integer
    current_week = league_info.get("settings", {}).get("last_scored_leg", 0)
    if current_week > 14:
        current_week = 14  # Cap at 14 weeks

    # Determine the maximum number of weeks for a given season
    def get_max_weeks(season, current_season, current_week):
        """
        Determine the maximum number of weeks for a given season.
        """
        if season == current_season:
            # For the current season, use the current week from the Sleeper API
            return current_week
        elif season in [2019, 2020]:
            # Cap at 13 weeks for 2019 and 2020
            return 13
        else:
            # Cap at 14 weeks for other seasons
            return 14
        
    
    for year in consts.LEAGUE_IDS.keys():
        
        year = int(year)  # Ensure year is an integer
        if year > cache.get("Last_Updated_Season", 0):
            # If the year is completely new, fetch all weeks
            max_weeks = get_max_weeks(year, current_season, current_week)
            weeks_to_update = range(1, max_weeks + 1)
        elif year < cache.get("Last_Updated_Season", 0):
            # If the year is in the past, skip updating
            continue
        else:
            # For the current year, determine the max weeks based on current season and week
            max_weeks = get_max_weeks(year, current_season, current_week)


        # Determine the range of weeks to update
        if year == current_season:
            last_updated_week = cache.get("Last_Updated_Week", 0)
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)

        print(f"Updating cache for season {year}, weeks: {list(weeks_to_update)}")

        # Fetch and update only the missing weeks for the year
        for week in weeks_to_update:
            if str(year) not in cache:
                cache[str(year)] = {}
            cache[str(year)][str(week)] = fetch_starters_for_week(year, week)

    # Update the last updated season and week
    cache["Last_Updated_Season"] = current_season
    cache["Last_Updated_Week"] = current_week

    # Save the updated cache to the file
    with open(STARTERS_CACHE_FILE, "w") as file:
        json.dump(cache, file, indent=4)

    return cache

def fetch_all_starters_data():
    """
    Fetch starters data for all years, weeks, and managers from the Sleeper API.
    """
    data = {}
    for year in consts.LEAGUE_IDS.keys():
        league_id = consts.LEAGUE_IDS[year]
        data[year] = {}  # Initialize year

        for week in range(1, 14):  # Assuming 14 weeks in the regular season
            data[year][week] = {}  # Initialize week

            sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
            if sleeper_response_users[1] != 200:
                continue  # Skip this week if the API call fails

            managers = sleeper_response_users[0]
            for manager in managers:
                real_name = consts.USERNAME_TO_REAL_NAME.get(manager['display_name'], "Unknown Manager")
                roster_id = get_roster_id(year, manager['user_id'])
                if not roster_id:
                    continue

                # Fetch starters for the manager
                starters_data = get_starters_data(league_id, roster_id, week)
                if not starters_data:
                    continue

                # Add manager's data for the week
                data[year][week][real_name] = starters_data

    return data

def get_roster_id(year, user_id):
    """
    Fetch the roster ID for a specific user in a given year.
    """
    league_id = consts.LEAGUE_IDS[year]
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
                player_score = matchup['players_points'].get(player_id, 0)
                player_position = PLAYER_IDS.get(player_id, {}).get('position', 'Unknown Position')

                # Add player data
                manager_data[player_name] = {
                    "points": player_score,
                    "position": player_position
                }

                # Update total points
                manager_data["Total_Points"] += player_score

            manager_data["Total_Points"] = float(Decimal(manager_data["Total_Points"]).quantize(Decimal('0.01')).normalize())

            return manager_data

    return None

def fetch_starters_for_week(season, week):
    """
    Fetch starters data for a specific season and week.
    """
    league_id = consts.LEAGUE_IDS[season]
    sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
    if sleeper_response_users[1] != 200:
        return {}  # Return empty data if the API call fails

    managers = sleeper_response_users[0]
    week_data = {}
    for manager in managers:
        real_name = consts.USERNAME_TO_REAL_NAME.get(manager['display_name'], "Unknown Manager")
        roster_id = get_roster_id(season, manager['user_id'])
        if not roster_id:
            continue

        # Fetch starters for the manager
        starters_data = get_starters_data(league_id, roster_id, week)
        if starters_data:
            week_data[real_name] = starters_data

    return week_data
