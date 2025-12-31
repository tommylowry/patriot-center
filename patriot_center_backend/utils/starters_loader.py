"""Starters cache builder/updater for Patriot Center.

Responsibilities:
- Maintain per-week starters and points per manager from Sleeper.
- Incrementally update a JSON cache, resuming from Last_Updated_* markers.
- Normalize totals to 2 decimals and resolve manager display names.

Performance:
- Minimizes API calls by:
  * Skipping already processed weeks (progress markers).
  * Only fetching week/user/roster/matchup data when needed.

Notes:
- Weeks are capped at 17 to include fantasy playoffs.
- Import-time execution at bottom warms the cache for downstream consumers.
"""
from decimal import Decimal
import copy

from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME, STARTERS_CACHE_FILE, PLAYERS_CACHE_FILE, VALID_OPTIONS_CACHE_FILE
from patriot_center_backend.utils.player_ids_loader import load_player_ids
from patriot_center_backend.utils.cache_utils import load_cache, save_cache, get_current_season_and_week
from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

PLAYER_IDS = load_player_ids()
MANAGER_METADATA = ManagerMetadataManager()

def load_starters_cache():
    """
    Load the persisted starters cache from disk.

    Returns:
        dict: Nested {season: {week: {manager: {...}}}}
    """
    cache = load_cache(STARTERS_CACHE_FILE)

    if not cache:
        raise RuntimeError("Starters cache is not initialized. Please run the cache updater.")

    cache.pop("Last_Updated_Season", None)
    cache.pop("Last_Updated_Week", None)
    return cache

def update_starters_cache():
    """
    Incrementally load/update starters cache and persist changes.

    Logic:
    - Resume from Last_Updated_* markers (avoids redundant API calls).
    - Cap weeks at 17 (include playoffs).
    - Only fetch missing weeks per season; break early if fully current.
    - Strip metadata before returning to callers.

    Returns:
        dict: Nested {season: {week: {manager: {...}}}}
    """
    cache = load_cache(STARTERS_CACHE_FILE)
    valid_options_cache = load_cache(VALID_OPTIONS_CACHE_FILE, initialize_with_last_updated_info=False)

    current_season, current_week = get_current_season_and_week()
    if current_week > 17:
        current_week = 17  # Regular season cap

    for year in LEAGUE_IDS.keys():
        last_updated_season = int(cache.get("Last_Updated_Season", 0))
        last_updated_week = cache.get("Last_Updated_Week", 0)

        # Skip previously finished seasons; reset week marker when advancing season.
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                cache['Last_Updated_Week'] = 0  # Reset for new season

        # Early exit if fully up to date (prevents unnecessary API calls).
        if last_updated_season == int(current_season):
            if last_updated_week == current_week:
                
                # Week 17 is the final playoff week; assign final placements if reached.
                if current_week == 17:
                    cache = retroactively_assign_team_placement_for_player(year, cache)
                
                break

        # For completed seasons, retroactively assign placements if not already done.
        # Skip the first season in LEAGUE_IDS since it may not have prior data.
        elif year != list(LEAGUE_IDS.keys())[0]:
            retroactively_assign_team_placement_for_player(year-1, cache)

        year = int(year)
        max_weeks = _get_max_weeks(year, current_season, current_week)

        if year == current_season or year == last_updated_season:
            last_updated_week = cache.get("Last_Updated_Week", 0)
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)

        if not weeks_to_update:
            continue

        print(f"Updating starters cache for season {year}, weeks: {list(weeks_to_update)}")

        for week in weeks_to_update:

            # Final week; assign final placements if reached.
            if week == max_weeks:
                retroactively_assign_team_placement_for_player(year, cache)

            cache.setdefault(str(year), {})
            valid_options_cache.setdefault(str(year), {})

            managers = valid_options_cache[str(year)].get("managers", [])
            players = valid_options_cache[str(year)].get("players", [])
            weeks = list(valid_options_cache[str(year)].keys())
            for key in weeks.copy():
                if not key.isdigit():
                    weeks.remove(key)
            positions = valid_options_cache[str(year)].get("positions", [])

            
            week_data, weekly_managers_summary_array, weekly_players_summary_array, weekly_positions_summary_array, week_valid_data = fetch_starters_for_week(year, week)
            for weekly_manager in weekly_managers_summary_array:
                if weekly_manager not in managers:
                    managers.append(weekly_manager)
            for weekly_player in weekly_players_summary_array:
                if weekly_player not in players:
                    players.append(weekly_player)
            for weekly_position in weekly_positions_summary_array:
                if weekly_position not in positions:
                    positions.append(weekly_position)
            
            weeks.append(str(week))
            
            valid_options_cache[str(year)]["managers"] = managers
            valid_options_cache[str(year)]["players"] = players
            valid_options_cache[str(year)]["weeks"] = weeks
            valid_options_cache[str(year)]["positions"] = positions
            valid_options_cache[str(year)][str(week)] = week_valid_data

            cache[str(year)][str(week)] = week_data

            MANAGER_METADATA.cache_week_data(str(year), str(week))

            # Advance progress markers (enables resumable incremental updates).
            cache['Last_Updated_Season'] = str(year)
            cache['Last_Updated_Week'] = week
            print(f"  Starters cache updated internally for season {year}, week {week}")


    save_cache(STARTERS_CACHE_FILE, cache)
    save_cache(VALID_OPTIONS_CACHE_FILE, valid_options_cache)
    MANAGER_METADATA.save()

    cache.pop("Last_Updated_Season", None)
    cache.pop("Last_Updated_Week", None)
    return cache

def _update_players_cache(player_meta, players_cache):
    """
    Add a new player to the players cache if not already present.

    Creates a cache entry with player metadata and URL-safe slug.
    Automatically persists changes to PLAYERS_CACHE_FILE.

    Args:
        player_meta (dict): Player metadata from PLAYER_IDS.
                           Expected keys: full_name, first_name, last_name,
                           position, team.
        players_cache (dict): Existing players cache to update.

    Returns:
        dict: Updated players_cache with new player added (if applicable).

    Side effects:
        Saves the updated cache to disk if a new player was added.
    """

    if player_meta.get("full_name") not in players_cache:
        
        slug = player_meta.get("full_name", "").lower()
        slug = slug.replace(" ", "%20")
        slug = slug.replace("'", "%27")
        
        players_cache[player_meta["full_name"]] = {
            "full_name": player_meta.get("full_name", ""),
            "first_name": player_meta.get("first_name", ""),
            "last_name": player_meta.get("last_name", ""),
            "position": player_meta.get("position", ""),
            "team": player_meta.get("team", ""),
            "slug": slug,
            "player_id": player_meta.get("player_id", "")
        }
        save_cache(PLAYERS_CACHE_FILE, players_cache)

    return players_cache

def _get_max_weeks(season, current_season, current_week):
    """
    Determine maximum playable weeks for a season.

    Rules:
    - Live season -> current_week (capped above).
    - 2019/2020 -> 16 (legacy rule set).
    - Other seasons -> 17 (regular season boundary).

    Returns:
        int: Max week to process for season.
    """
    if season == current_season:
        return current_week
    elif season in [2019, 2020]:
        return 16
    return 17

def _get_relevant_playoff_roster_ids(season, week, league_id):
    """
    Determine which rosters are participating in playoffs for a given week.

    Filters out regular season weeks and consolation bracket teams,
    returning only the roster IDs competing in the winners bracket.

    Rules:
    - 2019/2020: Playoffs start week 14 (rounds 1-3 for weeks 14-16).
    - 2021+: Playoffs start week 15 (rounds 1-3 for weeks 15-17).
    - Week 17 in 2019/2020 (round 4) is unsupported and raises an error.
    - Consolation bracket matchups (p=5) are excluded.

    Args:
        season (int): Target season year.
        week (int): Target week number.
        league_id (str): Sleeper league identifier.

    Returns:
        dict: {"round_roster_ids": [int]} or {} if regular season week.
              Empty dict signals no playoff filtering needed.

    Raises:
        ValueError: If week 17 in 2019/2020 or no rosters found for the round.
    """
    if int(season) <= 2020 and week <= 13:
        return {}
    if int(season) >= 2021 and week <= 14:
        return {}
    
    sleeper_response_playoff_bracket = fetch_sleeper_data(f"league/{league_id}/winners_bracket")
    if sleeper_response_playoff_bracket[1] == 200:
        sleeper_response_playoff_bracket = sleeper_response_playoff_bracket[0]

    if week == 14:
        round = 1
    elif week == 15:
        round = 2
    elif week == 16:
        round = 3
    else:
        round = 4

    if season >= 2021:
        round -= 1
    
    if round == 4:
        raise ValueError("Cannot get playoff roster IDs for week 17")
    
    relevant_roster_ids = {
        "round_roster_ids": [],
    }
    for matchup in sleeper_response_playoff_bracket:
        if matchup['r'] == round:
            if "p" in matchup and matchup['p'] == 5:
                continue  # Skip consolation match
            relevant_roster_ids['round_roster_ids'].append(matchup['t1'])
            relevant_roster_ids['round_roster_ids'].append(matchup['t2'])

    if len(relevant_roster_ids['round_roster_ids']) == 0:
        raise ValueError("Cannot get playoff roster IDs for the given week")
    
    return relevant_roster_ids

def _get_playoff_placement(season):
    """
    Retrieve final playoff placements (1st, 2nd, 3rd) for a completed season.

    Fetches the winners bracket from Sleeper API and determines:
    - 1st place: Winner of championship match (last-1 matchup winner)
    - 2nd place: Loser of championship match
    - 3rd place: Winner of 3rd place match (last matchup winner)

    Args:
        season (int): Target season year (must be completed).

    Returns:
        dict: {manager_real_name: placement_int}
              Example: {"Tommy": 1, "Mike": 2, "Davey": 3}
              Empty dict on API failure.

    API calls:
        - league/{league_id}/winners_bracket
        - league/{league_id}/rosters
        - league/{league_id}/users
    """
    league_id = LEAGUE_IDS[int(season)]

    sleeper_response_playoff_bracket = fetch_sleeper_data(f"league/{league_id}/winners_bracket")
    if sleeper_response_playoff_bracket[1] == 200:
        sleeper_response_playoff_bracket = sleeper_response_playoff_bracket[0]
    else:
        print("Failed to fetch playoff bracket data")
        return {}

    sleeper_response_rosters = fetch_sleeper_data(f"league/{league_id}/rosters")
    if sleeper_response_rosters[1] == 200:
        sleeper_response_rosters = sleeper_response_rosters[0]
    else:
        print("Failed to fetch rosters data")
        return {}
    
    sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
    if sleeper_response_users[1] == 200:
        sleeper_response_users = sleeper_response_users[0]
    else:
        print("Failed to fetch users data")
        return {}
    
    
    championship = sleeper_response_playoff_bracket[-2]
    third_place = sleeper_response_playoff_bracket[-1]
    
    placement = {}

    
    for manager in sleeper_response_users:
        for roster in sleeper_response_rosters:
            if manager['user_id'] == roster['owner_id']:
                if roster['roster_id'] == championship['w']:
                    placement[USERNAME_TO_REAL_NAME[manager['display_name']]] = 1
                if roster['roster_id'] == championship['l']:
                    placement[USERNAME_TO_REAL_NAME[manager['display_name']]] = 2
                if roster['roster_id'] == third_place['w']:
                   placement[USERNAME_TO_REAL_NAME[manager['display_name']]] = 3

    return placement
    

    


def fetch_starters_for_week(season, week):
    """
    Build per-manager starter/points map for a given season/week.

    API calls:
        - users
        - rosters
        - matchups/{week}

    Returns:
        dict: real_manager_name -> {player_name: {points, position}, Total_Points}
              Empty dict on API failure.
    """
    league_id = LEAGUE_IDS[int(season)]
    sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
    if sleeper_response_users[1] != 200:
        return {}, [], [], [], {}

    sleeper_response_rosters = fetch_sleeper_data(f"league/{league_id}/rosters")
    if sleeper_response_rosters[1] != 200:
        return {}, [], [], [], {}

    sleeper_response_matchups = fetch_sleeper_data(f"league/{league_id}/matchups/{week}")
    if sleeper_response_matchups[1] != 200:
        return {}, [], [], [], {}
    
    playoff_roster_ids = _get_relevant_playoff_roster_ids(season, week, league_id)
    
    managers_summary_array = []
    players_summary_array = []
    positions_summary_array = []
    week_valid_data = {}

    managers = sleeper_response_users[0]
    week_data = {}
    for manager in managers:
        players_summary_array_per_manager   = []
        positions_summary_array_per_manager = []
        
        if manager['display_name'] not in USERNAME_TO_REAL_NAME:
            raise ValueError (f"{manager['display_name']} not in {USERNAME_TO_REAL_NAME.keys()}")
        
        real_name = USERNAME_TO_REAL_NAME[manager['display_name']]

        # Historical correction: In 2019 weeks 1-3, Tommy played under Cody's roster.
        # Reassign those weeks from Cody to Tommy for accurate records.
        if int(season) == 2019 and week < 4 and real_name == "Cody":
            real_name = "Tommy"

        roster_id = get_roster_id(sleeper_response_rosters, manager['user_id'])
        if roster_id is None:
            # Fallback: In 2024, Davey's user_id doesn't match their roster owner_id.
            # Hardcode roster_id=4 as a known correction for this mismatch.
            if int(season) == 2024 and real_name == "Davey":
                roster_id = 4
        
        # Initialize manager metadata for this season/week before skipping playoff filtering.
        MANAGER_METADATA.set_roster_id(real_name, str(season), str(week), roster_id, playoff_roster_ids, sleeper_response_matchups[0])

        if not roster_id:
            continue  # Skip unresolved roster

        # During playoff weeks, only include rosters actively competing in that round.
        # This filters out teams eliminated or in consolation bracket.
        if playoff_roster_ids != {} and roster_id not in playoff_roster_ids['round_roster_ids']:
            continue  # Skip non-playoff rosters in playoff weeks

        starters_data, players_summary_array_per_manager, positions_summary_array_per_manager = get_starters_data(sleeper_response_matchups,
                                                                                                                  roster_id,
                                                                                                                  players_summary_array_per_manager, 
                                                                                                                  positions_summary_array_per_manager)
        if starters_data:
            week_data[real_name] = starters_data
            week_valid_data[real_name] = { "players": players_summary_array_per_manager, "positions": positions_summary_array_per_manager }

            managers_summary_array.append(real_name)
            for player in players_summary_array_per_manager:
                if player not in players_summary_array:
                    players_summary_array.append(player)
            for position in positions_summary_array_per_manager:
                if position not in positions_summary_array:
                    positions_summary_array.append(position)
    
    week_valid_data["managers"] = managers_summary_array
    week_valid_data["players"] = players_summary_array
    week_valid_data["positions"] = positions_summary_array

    return week_data, managers_summary_array, players_summary_array, positions_summary_array, week_valid_data

def get_roster_id(sleeper_response_rosters, user_id):
    """
    Resolve a roster_id for the given user_id.

    Args:
        sleeper_response_rosters (tuple): (payload, status_code)
        user_id (str): Sleeper user identifier.

    Returns:
        int | None: roster_id if found, else None.
    """
    rosters = sleeper_response_rosters[0]
    for roster in rosters:
        if roster['owner_id'] == user_id:
            return roster['roster_id']
    return None

def get_starters_data(sleeper_response_matchups,
                      roster_id,
                      players_summary_array,
                      positions_summary_array):
    """
    Extract starters + total points for one roster/week.

    Filters:
        - Unknown players or positions skipped.
        - Total normalized to 2 decimals.

    Args:
        sleeper_response_matchups (tuple): (payload, status_code)
        roster_id (int): Target roster identifier.

    Returns:
        dict | None: {player_name: {points, position}, Total_Points} or None if not found.
    """

    players_cache = load_cache(PLAYERS_CACHE_FILE, initialize_with_last_updated_info=False)

    matchups = sleeper_response_matchups[0]
    for matchup in matchups:
        if matchup['roster_id'] == roster_id:
            manager_data = {"Total_Points": 0.0}
            for player_id in matchup['starters']:
                
                player_meta = PLAYER_IDS.get(player_id, {})

                player_name = player_meta.get('full_name')
                if not player_name:
                    continue  # Skip unknown player
                player_position = player_meta.get('position')
                if not player_position:
                    continue  # Skip if no position resolved

                if player_name not in players_summary_array:
                    players_summary_array.append(player_name)
                if player_position not in positions_summary_array:
                    positions_summary_array.append(player_position)
                
                player_meta['player_id'] = player_id

                _update_players_cache(player_meta, players_cache)

                player_score = matchup['players_points'].get(player_id, 0)

                manager_data[player_name] = {
                    "points": player_score,
                    "position": player_position,
                    "player_id": player_id
                }

                manager_data["Total_Points"] += player_score

            manager_data["Total_Points"] = float(
                Decimal(manager_data["Total_Points"]).quantize(Decimal('0.01')).normalize()
            )
            return manager_data, players_summary_array, positions_summary_array
    return {}, players_summary_array, positions_summary_array


def retroactively_assign_team_placement_for_player(season, starters_cache):
    """
    Retroactively assign team placement for players in playoff weeks.

    Args:
        season (int): Target season.
        week (int): Target week.
        starters_cache (dict): Loaded starters cache.

    Returns:
        dict: Updated starters cache with placements assigned.
    """
    placements = _get_playoff_placement(season)
    if not placements:
        return starters_cache
    
    MANAGER_METADATA.set_playoff_placements(placements, str(season))

    weeks = ['15', '16', '17']
    if season <= 2020:
        weeks = ['14', '15', '16']

    need_to_print = True
    season_str = str(season)
    for week in weeks:
        for manager in starters_cache.get(season_str, {}).get(week, {}):
            if manager in placements:
                for player in starters_cache[season_str][week][manager]:
                    if player != "Total_Points":
                        
                        # placement already assigned
                        if "placement" in starters_cache[season_str][week][manager][player]:
                            return starters_cache
                        
                        if need_to_print:
                            print(f"New placements found: {placements}, retroactively applying placements.")
                            need_to_print = False
                        
                        starters_cache[season_str][week][manager][player]['placement'] = placements[manager]
    
    return starters_cache