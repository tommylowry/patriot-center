"""Utilities to build and maintain the ffWAR cache for Patriot Center.

This module:
- Loads supporting caches at import time (replacement scores and starters).
- Determines the current fantasy season/week.
- Loads an ffWAR cache JSON file and incrementally updates it by year/week.
- Persists the updated cache back to disk.

Algorithm summary:
- For each unprocessed week, derive per-position player scores.
- Simulate hypothetical matchups replacing each player with a positional replacement average.
- ffWAR = (net simulated wins difference) / (total simulations), rounded to 3 decimals.

Notes:
- Import-time cache loading performs I/O and possible network calls.
- Weeks are capped at 17 (include playoff data).
"""

from patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME

from patriot_center_backend.cache import get_cache_manager
from patriot_center_backend.utils.helpers import fetch_sleeper_data, get_current_season_and_week


CACHE_MANAGER = get_cache_manager()

PLAYER_DATA_CACHE  = CACHE_MANAGER.get_player_data_cache(for_update=True)
REPLACEMENT_SCORES = CACHE_MANAGER.get_replacement_score_cache()
STARTERS_CACHE     = CACHE_MANAGER.get_starters_cache()
PLAYER_IDS         = CACHE_MANAGER.get_player_ids_cache()


def update_player_data_cache():
    """
    Incrementally update ffWAR cache.

    Process:
        - Iterate seasons; compute missing weeks only.
        - Cap weeks at 17.
        - Store progress via Last_Updated_* markers.
    """
    # Dynamically determine the current season and week according to Sleeper API/util logic.
    current_season, current_week = get_current_season_and_week()
    if current_week > 17:
        # Cap at the end of the fantasy regular season to keep ffWAR comparable across years.
        current_week = 17  # Cap the current week at 17

    # Process all years configured for leagues; this drives which seasons we consider for updates.
    years = list(LEAGUE_IDS.keys())

    for year in years:
        # Read progress markers from the cache to support incremental updates and resumability.
        # Cast Last_Updated_Season to int to allow numeric comparison with `year`.
        last_updated_season = int(PLAYER_DATA_CACHE.get("Last_Updated_Season", 0))
        last_updated_week = PLAYER_DATA_CACHE.get("Last_Updated_Week", 0)

        # Skip years that are already fully processed based on the last recorded season.
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                PLAYER_DATA_CACHE["Last_Updated_Week"] = 0  # Reset the week if moving to a new year

        # If the cache is already up-to-date for the current season and week, stop processing.
        if last_updated_season == int(current_season) and last_updated_week == current_week:
            return

        year = int(year)  # Ensure year is an integer
        max_weeks = _get_max_weeks(year, current_season, current_week)

        # Determine the range of weeks to update.
        if year == current_season or year == last_updated_season:
            last_updated_week = PLAYER_DATA_CACHE.get("Last_Updated_Week", 0)
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)

        if list(weeks_to_update) == []:
            continue
        
        print(f"Updating Player Data cache for season {year}, weeks: {list(weeks_to_update)}")

        roster_ids = _get_roster_ids(year)

        # Fetch and update only the missing weeks for the year.
        for week in weeks_to_update:
            if str(year) not in PLAYER_DATA_CACHE:
                PLAYER_DATA_CACHE[str(year)] = {}

            # Fetch ffWAR for the week.
            PLAYER_DATA_CACHE[str(year)][str(week)] = _fetch_ffWAR(year, week, roster_ids)

            # Update the metadata for the last updated season and week.
            PLAYER_DATA_CACHE["Last_Updated_Season"] = str(year)
            PLAYER_DATA_CACHE["Last_Updated_Week"] = week

            print("  Player Data cache updated internally for season {}, week {}".format(year, week))

    # Save the updated cache to the file.
    CACHE_MANAGER.save_player_data_cache()

    # Reload to remove the metadata fields
    CACHE_MANAGER.get_player_data_cache(force_reload=True)

def _get_max_weeks(season, current_season, current_week):
    """
    Max playable weeks per season:
        - Live season: current_week
        - 2019/2020: 16
        - Others: 17
    """
    if season == current_season:
        return current_week  # Use the current week for the current season
    elif season in [2019, 2020]:
        return 16  # Cap at 16 weeks for 2019 and 2020
    else:
        return 17  # Cap at 17 weeks for other seasons

def _fetch_ffWAR(season, week, roster_ids):
    """
    Build positional score structures then compute ffWAR for one week.

    Returns:
        dict: player -> {ffWAR, manager, position}
    """
    weekly_data = STARTERS_CACHE[str(season)][str(week)]

    players = {
        "QB":  {},
        "RB":  {},
        "WR":  {},
        "TE":  {},
        "K":   {},
        "DEF": {}
    }
    
    for manager in weekly_data:
        for position in players:
            
            old_players_position = players[position]
            old_players_position[manager] = {'total_points': weekly_data[manager]['Total_Points'], 'players': {}}
            players[position] = old_players_position
            
        for player in weekly_data[manager]:
            if player == 'Total_Points':
                continue

            position = weekly_data[manager][player]['position']
            players[position][manager]['players'][player] = weekly_data[manager][player]['points']
                

    ffWAR_results = {}
    all_player_scores   = _get_all_player_scores(season, week)
    all_rostered_players = _get_all_rostered_players(roster_ids, season, week)
    
    for position in players:
        calculated_ffWAR = _calculate_ffWAR_position(players[position], season, week, position, all_player_scores[position], all_rostered_players)
        if calculated_ffWAR == {}:
            continue
        for player_id in calculated_ffWAR:
            ffWAR_results[player_id] = calculated_ffWAR[player_id]
    
    # sort ffWAR_position by ffWAR descending, then by name ascending
    ffWAR_results = dict(sorted(ffWAR_results.items(), key=lambda item: (-item[1]['ffWAR'], item[1]['name'])))

    return ffWAR_results

def _calculate_ffWAR_position(scores, season, week, position, all_player_scores, all_rostered_players):
    """
    Simulate ffWAR for one position group.

    Replacement baseline:
        Uses <position>_3yr_avg from replacement score cache.

    Returns:
        dict: player -> {ffWAR, manager, position}
    """
    # Get the 3-year rolling average replacement score for this position
    key = f"{position}_3yr_avg"
    replacement_average = REPLACEMENT_SCORES[str(season)][str(week)][key]


    # Calculate the average score across all players at this position this week
    # This helps normalize scores when simulating replacement scenarios
    num_players = 0
    total_position_score = 0.0
    for manager in scores:
        num_players += len(scores[manager]['players'])
        for player in scores[manager]['players']:
            total_position_score += scores[manager]['players'][player]

    if num_players == 0:
        return {}  # No players at this position this week

    average_player_score_this_week = total_position_score / num_players


    # Pre-compute normalized scores for each manager
    # These values are used in the simulation to isolate positional impact
    for manager in scores:

        # Calculate this manager's average score at this position
        player_total_for_manager = 0.0
        for player in scores[manager]['players']:
            player_total_for_manager += scores[manager]['players'][player]

        if len(scores[manager]['players']) == 0:
            player_average_for_manager = 0
        else:
            player_average_for_manager = player_total_for_manager / len(scores[manager]['players'])

        # Store manager's total points minus their positional contribution
        # This represents the manager's "baseline" without this position's impact
        scores[manager]['total_minus_position'] = scores[manager]["total_points"] - player_average_for_manager

        # Store normalized weighted score (baseline + league average at position)
        # Used as opponent's score in simulations
        scores[manager]['weighted_total_score'] = scores[manager]["total_points"] - player_average_for_manager  + average_player_score_this_week

    # Simulate head-to-head matchups to compute ffWAR for each player
    ffWAR_position = {}

    for player_id in all_player_scores:
        
        # Player's Full Name
        player = all_player_scores[player_id]['name']
        

        # Image URL
        image_url = f"https://sleepercdn.com/content/nfl/players/{player_id}.jpg"
        if position == "DEF":
            image_url = f"https://sleepercdn.com/images/team_logos/nfl/{player_id.lower()}.png"
        


        # Determine if this player is rostered and started, and by whom
        player_data_manager_value = None
        started                   = False
        for manager in all_rostered_players:
            if player_id in all_rostered_players[manager]:
                player_data_manager_value = manager
                
                # Some managers may roster but not count in the scores if they didn't play in the playoffs
                if player in scores.get(manager, {}).get('players', {}):
                    started = True
                break
        
        player_score = all_player_scores[player_id]['score']
        
        player_data = {
            "name":      all_player_scores[player_id]['name'],
            "image_url": image_url,
            "score":     all_player_scores[player_id]['score'],
            "ffWAR":     0.0,
            "position":  position,
            "manager":   player_data_manager_value,
            "started":   started
        }

        # Initialize counters for simulated head-to-head comparisons
        num_simulated_games = 0
        num_wins = 0  # Net wins: +1 when player adds a win, -1 when replacement would win instead

        # Simulate all possible manager pairings with this player
        for manager_playing in scores:
            for manager_opposing in scores:
                if manager_playing == manager_opposing:
                    continue  # Skip self-matchups

                # Opponent's normalized score (baseline + position average)
                simulated_opponent_score = scores[manager_opposing]['weighted_total_score']

                # Manager's score WITH this player at this position
                simulated_player_score = scores[manager_playing]['total_minus_position'] + player_score

                # Manager's score with REPLACEMENT-level player at this position
                simulated_replacement_score = scores[manager_playing]['total_minus_position'] + replacement_average

                # Case 1: Player wins but replacement would lose (player adds a win)
                if (simulated_player_score > simulated_opponent_score) and (simulated_replacement_score < simulated_opponent_score):
                    num_wins += 1

                # Case 2: Player loses but replacement would win (player costs a win)
                if (simulated_player_score < simulated_opponent_score) and (simulated_replacement_score > simulated_opponent_score):
                    num_wins -= 1

                # Case 3 & 4: Both win or both lose (no impact on outcome, ffWAR = 0 contribution)

                num_simulated_games += 1

        # Calculate final ffWAR score as win rate differential
        if num_simulated_games == 0:
            ffWAR_score = 0.0
        else:
            ffWAR_score = round(num_wins / num_simulated_games, 3)

            # Playoff adjustment: scale down by 1/3 since only 4 of 12 teams play each week
            # 2020 and earlier: playoffs start week 14
            # 2021 and later: playoffs start week 15
            if season <= 2020 and week >=14 or season >=2021 and week >=15:
                ffWAR_score = round (ffWAR_score / 3, 3)
        
        player_data["ffWAR"] = ffWAR_score

        ffWAR_position[player_id] = player_data

    return ffWAR_position

def _get_all_player_scores(year, week):
    """
    Fetch and calculate fantasy scores for all NFL players in a given week.

    This function retrieves raw stats from the Sleeper API for the specified season
    and week, then calculates each player's fantasy score based on the league's
    scoring settings. Players are grouped by position for easier processing.

    Args:
        year (int): The NFL season year (e.g., 2024).
        week (int): The week number (1-17).

    Returns:
        dict: Nested dictionary with structure:
            {
                "QB": {
                    "player_id": {"score": float, "name": str},
                    ...
                },
                "RB": {...},
                "WR": {...},
                "TE": {...},
                "K": {...},
                "DEF": {...}
            }

        Each position contains all players who played that week (gp > 0),
        with their calculated fantasy score and full name.

    Raises:
        Exception: If the Sleeper API call fails (non-200 response).

    Notes:
        - Players with gp (games played) = 0 are excluded.
        - TEAM_ entries are skipped (not real players).
        - Defense players with numeric IDs are excluded.
        - Handles edge case of traded players with modified IDs.
    """
    # Fetch data from the Sleeper API for the given season and week
    week_data        = fetch_sleeper_data(f"stats/nfl/regular/{year}/{week}")
    scoring_settings = fetch_sleeper_data(f"league/{LEAGUE_IDS.get(year)}")['scoring_settings']

    final_week_scores = {
        "QB":  {},
        "RB":  {},
        "WR":  {},
        "TE":  {},
        "K":   {},
        "DEF": {} 
    }
    
    for player_id in week_data:

        if "TEAM_" in player_id:
            continue
        
        # Zach Ertz traded from PHI to ARI causes his player ID to be weird sometimes
        if player_id not in PLAYER_IDS:
            only_numeric = ''.join(filter(str.isdigit, player_id))
            if only_numeric in PLAYER_IDS:
                player_name = PLAYER_IDS[only_numeric]["full_name"]
                print(f"Weird possibly traded player id encountered in replacement score calculation for season {year} week {week}, probably {player_name}, using {only_numeric} instead of {player_id}")
                player_id = only_numeric
            else:
                print("Unknown numeric player id encountered in replacement score calculation for:", player_id)
                continue

        # Get player information from PLAYER_IDS
        player_info = PLAYER_IDS[player_id]

        # If the player ID is numeric and the position is DEF, skip processing
        if player_id.isnumeric() and player_info["position"] == "DEF":
            continue
        
        if player_info["position"] in list(final_week_scores.keys()):
            player_data = week_data[player_id]
            
            if "gp" not in player_data or player_data["gp"] == 0.0:
                continue

            player_score = _calculate_player_score(player_data, scoring_settings)
            # Add the player's points to the appropriate position list
            final_week_scores[player_info["position"]][player_id] = {
                "score": player_score,
                "name": player_info["full_name"]
            }
    

    return final_week_scores

def _calculate_player_score(player_data, scoring_settings):
    """
    Calculate a player's total fantasy score based on their stats and league scoring settings.

    Iterates through all stats in player_data and multiplies each stat value by its
    corresponding points-per-unit value from scoring_settings. Only stats that exist
    in the scoring_settings are counted.

    Args:
        player_data (dict): Player's raw stats for the week.
            Example: {"pass_yd": 300, "pass_td": 3, "rush_yd": 20, "gp": 1}

        scoring_settings (dict): League's scoring rules mapping stat keys to point values.
            Example: {"pass_yd": 0.04, "pass_td": 4, "rush_yd": 0.1}

    Returns:
        float: The player's total fantasy points, rounded to 2 decimal places.

    Example:
        >>> player_data = {"pass_yd": 300, "pass_td": 2, "gp": 1}
        >>> scoring_settings = {"pass_yd": 0.04, "pass_td": 4}
        >>> _calculate_player_score(player_data, scoring_settings)
        20.0  # (300 * 0.04) + (2 * 4) = 12 + 8 = 20.0

    Notes:
        - Stats not in scoring_settings are ignored (e.g., "gp", "player_id").
        - Supports negative point values (e.g., interceptions: -2 per int).
        - Always rounds to exactly 2 decimal places.
    """
    total_score = 0.0
    for stat_key, stat_value in player_data.items():
        # Only count stats that have scoring values defined in league settings
        if stat_key in scoring_settings:
            points_per_unit = scoring_settings[stat_key]
            total_score += stat_value * points_per_unit
    return round(total_score, 2)

def _get_roster_ids(season):
    """
    Build a mapping of roster IDs to real manager names for a given season.

    This function performs a two-step API query:
    1. Fetches all users in the league to map user_id -> real name
    2. Fetches all rosters to map roster_id -> user_id

    Then combines them to create roster_id -> real_name mapping.

    Args:
        season (int): The NFL season year (e.g., 2024).

    Returns:
        dict: Mapping of roster IDs to manager real names.
            Example: {1: "Tommy", 2: "Mike", 3: "James"}

    Notes:
        - Uses USERNAME_TO_REAL_NAME constant to convert display names to real names.
        - Special case: If owner_id is None, defaults to "Davey" (known data issue).
        - Roster IDs are integers from the Sleeper API.
    """
    user_ids = {}
    users_data_response = fetch_sleeper_data(f"league/{LEAGUE_IDS[season]}/users")
    for user in users_data_response:
        user_ids[user['user_id']] = USERNAME_TO_REAL_NAME[user['display_name']]
    
    roster_ids = {}
    user_rosters_data_response = fetch_sleeper_data(f"league/{LEAGUE_IDS[season]}/rosters")
    for user in user_rosters_data_response:
        
        # Handle a known case where owner_id is None
        if not user['owner_id']:
            roster_ids[user['roster_id']] = "Davey"
            continue
        
        roster_ids[user['roster_id']] = user_ids[user['owner_id']]

    return roster_ids

def _get_all_rostered_players(roster_ids, season, week):
    """
    Get all players rostered by each manager for a specific week's matchup.

    Fetches matchup data from the Sleeper API and maps each manager to their
    list of rostered players for that week. Handles a known historical data
    inconsistency in early 2019.

    Args:
        roster_ids (dict): Mapping of roster_id -> manager_name.
            Example: {1: "Tommy", 2: "Mike"}

        season (int): The NFL season year (e.g., 2024).

        week (int): The week number (1-17).

    Returns:
        dict: Mapping of manager names to lists of player IDs they rostered.
            Example: {
                "Tommy": ["4034", "1234", "5678"],
                "Mike": ["9999", "8888"]
            }

    Notes:
        - Uses deep copy to avoid mutating the input roster_ids.
        - Known issue: In 2019 weeks 1-3, "Cody" roster is reassigned to "Tommy"
          due to a historical league roster transfer.
        - Player IDs are strings from the Sleeper API.
    """
    import copy
    imported_roster_ids = copy.deepcopy(roster_ids)

    # Handle known issue with Tommy's roster ID in early 2019 weeks
    # In weeks 1-3 of 2019, Cody's roster should be attributed to Tommy
    if int(season) == 2019 and int(week) <=3:
        for key in roster_ids:
            if roster_ids[key] == "Cody":
                imported_roster_ids[key] = "Tommy"
                break
    
    rostered_players = {}

    
    matchup_data_response = fetch_sleeper_data(f"league/{LEAGUE_IDS[season]}/matchups/{week}")

    for matchup in matchup_data_response:
        rostered_players[imported_roster_ids[matchup['roster_id']]] = matchup['players']
    
    return rostered_players