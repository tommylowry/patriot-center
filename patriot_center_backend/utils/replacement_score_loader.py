from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.utils.player_ids_loader import load_player_ids
from patriot_center_backend.utils.cache_utils import load_cache, save_cache, get_current_season_and_week

# Constants
REPLACEMENT_SCORE_FILE = "patriot_center_backend/data/replacement_score.json"
PLAYER_IDS = load_player_ids()

def load_or_update_replacement_score_cache():
    
    # Load existing cache or initialize a new one
    cache = load_cache(REPLACEMENT_SCORE_FILE)

    # Dynamically determine the current season and week
    current_season, current_week = get_current_season_and_week()
    if current_week > 18:
        current_week = 18

    # Process all years in LEAGUE_IDS with extra years for replacement score
    years = list(LEAGUE_IDS.keys())
    first_year = min(years)
    years.extend([first_year - 3, first_year - 2, first_year - 1])
    years = sorted(years)

    for year in years:
        
        # Get the last updated season and week from the cache
        last_updated_season = int(cache.get("Last_Updated_Season", 0))
        last_updated_week   = cache.get("Last_Updated_Week", 0)
        
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                cache['Last_Updated_Week'] = 0
        
        if last_updated_season == int(current_season) and last_updated_week == current_week:
            break

        year = int(year)  # Ensure year is an integer
        max_weeks = _get_max_weeks(year, current_season, current_week)

        # Determine the range of weeks to update
        if year == current_season or year == last_updated_season:
            last_updated_week = cache.get("Last_Updated_Week", 0)
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)

        if list(weeks_to_update) == []:
            continue

        print(f"Updating replacement score cache for season {year}, weeks: {list(weeks_to_update)}")

        # Fetch and update only the missing weeks for the year
        for week in weeks_to_update:
            if str(year) not in cache:
                cache[str(year)] = {}
            
            # If there is data from three years ago, we can also compute the 3-year average
            cache[str(year)][str(week)] = _fetch_replacement_score_for_week(year, week)
            
            # Compute the 3-year average if data from three years ago exists
            if (str(year-3) in cache):
                cache[str(year)][str(week)] = _get_three_yr_avg(year, week, cache)

            cache['Last_Updated_Season'] = str(year)
            cache['Last_Updated_Week'] = week

            print("  Replacement score cache updated internally for season {}, week {}".format(year, week))

    # Save the updated cache to the file
    save_cache(REPLACEMENT_SCORE_FILE, cache)

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
    """
    if season == current_season:
        return current_week  # Use the current week for the current season
    elif season <= 2020:
        return 17  # Cap at 17 weeks for seasons 2020 and earlier
    else:
        return 18  # Cap at 18 weeks for other seasons

def _fetch_replacement_score_for_week(season, week):
    sleeper_response_week_data = fetch_sleeper_data(f"stats/nfl/regular/{season}/{week}")
    if sleeper_response_week_data[1] != 200:
        raise Exception(f"Failed to fetch week data from Sleeper API for season {season}, week {week}")
    
    # Get the number of byes for the week
    byes = 32
    week_scores = {
        "QB": [],
        "RB": [],
        "WR": [],
        "TE": []
    }
    week_data = sleeper_response_week_data[0]
    for player_id in week_data:
        
        if "TEAM_" in player_id:
            byes -= 1
            continue
        elif player_id not in PLAYER_IDS:
            continue
        
        player_info = PLAYER_IDS[player_id]
        if (player_info['position'] in week_scores) and ('pts_half_ppr' in week_data[player_id]):
            week_scores[player_info['position']].append(week_data[player_id]['pts_half_ppr'])
    
    for position in week_scores:
        week_scores[position].sort(reverse=True)
    
    # Determine the replacement scores: QB13, RB31, WR31, TE13
    week_scores["QB"] = week_scores["QB"][12]
    week_scores["RB"] = week_scores["RB"][30]
    week_scores["WR"] = week_scores["WR"][30]
    week_scores["TE"] = week_scores["TE"][12]
    
    # Add number of byes
    week_scores["byes"] = byes

    return week_scores


def _get_three_yr_avg(season, week, cache):

    current_week_scores = cache[str(season)][str(week)]
    byes = current_week_scores["byes"]

    three_yr_season_scores  = {}
    three_yr_season_average = {}
    for current_week_position in current_week_scores:
        if current_week_position == "byes":
            continue
        three_yr_season_scores[current_week_position] = {}
        three_yr_season_average[current_week_position] = {}
    

    for past_year in [season, season-1, season-2, season-3]:

        # Determine the weeks to consider for the past year
        weeks = range(1, 18 if past_year <= 2020 else 19)

        # For the current season, only consider up to the current week
        if past_year == season:
            weeks = range(1, week+1)
        
        # For the season three years ago, only consider from the current week to the end of the season
        if past_year == season-3:
            weeks = range(week, 18 if past_year <= 2020 else 19)
        
        for w in weeks:
            past_byes = cache[str(past_year)][str(w)]["byes"]
            for past_position in three_yr_season_scores:
                past_score = cache[str(past_year)][str(w)][past_position]
                
                if past_byes not in three_yr_season_scores[past_position]:
                    three_yr_season_scores[past_position][past_byes] = []
                
                three_yr_season_scores[past_position][past_byes].append(past_score)



    # Compute the average replacement scores for each position and bye count
    for past_position in three_yr_season_scores:
        for past_byes in three_yr_season_scores[past_position]:
            avg = sum(three_yr_season_scores[past_position][past_byes]) / len(three_yr_season_scores[past_position][past_byes])
            three_yr_season_average[past_position][past_byes] = avg

    # Ensure monotonicity: more byes should not lead to lower replacement scores
    three_yr_season_average_copy = three_yr_season_average.copy()
    list_of_byes = sorted(three_yr_season_average["QB"].keys())
    for past_position in three_yr_season_average_copy:
        for i in range(len(list_of_byes)-1, 0, -1):
            if three_yr_season_average[past_position][list_of_byes[i]] > three_yr_season_average[past_position][list_of_byes[i-1]]:
                three_yr_season_average[past_position][list_of_byes[i-1]] = three_yr_season_average[past_position][list_of_byes[i]]

    for past_position in three_yr_season_average:
        new_key = f'{past_position}_3yr_avg'
        current_week_scores[new_key] = three_yr_season_average[past_position][byes]


    return current_week_scores


load_or_update_replacement_score_cache()