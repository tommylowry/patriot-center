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
- Weeks are capped at 14 (exclude playoff data).
"""

import os
from patriot_center_backend.utils.replacement_score_loader import load_or_update_replacement_score_cache
from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache
from patriot_center_backend.utils.cache_utils import load_cache, save_cache, get_current_season_and_week
from patriot_center_backend.constants import LEAGUE_IDS, FFWAR_CACHE_FILE

# Constants
# Load and memoize supporting datasets at import time so subsequent calls can reuse them.
# Be aware: these may perform network and disk I/O during import.
REPLACEMENT_SCORES   = load_or_update_replacement_score_cache()
PLAYER_DATA          = load_or_update_starters_cache()


def load_or_update_ffWAR_cache():
    """
    Incrementally update ffWAR cache.

    Process:
        - Iterate seasons; compute missing weeks only.
        - Cap weeks at 17.
        - Store progress via Last_Updated_* markers.
    """
    # Load existing cache or initialize a new one if the file does not exist/cannot be parsed.
    cache = load_cache(FFWAR_CACHE_FILE)

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
        last_updated_season = int(cache.get("Last_Updated_Season", 0))
        last_updated_week = cache.get("Last_Updated_Week", 0)

        # Skip years that are already fully processed based on the last recorded season.
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                cache["Last_Updated_Week"] = 0  # Reset the week if moving to a new year

        # If the cache is already up-to-date for the current season and week, stop processing.
        if last_updated_season == int(current_season) and last_updated_week == current_week:
            break

        year = int(year)  # Ensure year is an integer
        max_weeks = _get_max_weeks(year, current_season, current_week)

        # Determine the range of weeks to update.
        if year == current_season or year == last_updated_season:
            last_updated_week = cache.get("Last_Updated_Week", 0)
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)

        if list(weeks_to_update) == []:
            continue

        print(f"Updating replacement score cache for season {year}, weeks: {list(weeks_to_update)}")

        # Fetch and update only the missing weeks for the year.
        for week in weeks_to_update:
            if str(year) not in cache:
                cache[str(year)] = {}

            # Fetch ffWAR for the week.
            cache[str(year)][str(week)] = _fetch_ffWAR(year, week)

            # Update the metadata for the last updated season and week.
            cache["Last_Updated_Season"] = str(year)
            cache["Last_Updated_Week"] = week

            print("  ffWAR cache updated internally for season {}, week {}".format(year, week))

    # Save the updated cache to the file.
    save_cache(FFWAR_CACHE_FILE, cache)

    # Remove metadata before returning.
    # These fields are used internally for tracking updates but are not part of the final cache returned.
    cache.pop("Last_Updated_Season", None)
    cache.pop("Last_Updated_Week", None)

    return cache


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

def _fetch_ffWAR(season, week):
    """
    Build positional score structures then compute ffWAR for one week.

    Returns:
        dict: player -> {ffWAR, manager, position}
    """
    weekly_data = PLAYER_DATA[str(season)][str(week)]

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
    for position in players:
        calculated_ffWAR = _calculate_ffWAR_position(players[position], season, week, position)
        if calculated_ffWAR == {}:
            continue
        for player in calculated_ffWAR:
            ffWAR_results[player] = calculated_ffWAR[player]

    return ffWAR_results

def _calculate_ffWAR_position(scores, season, week, position):
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
    for real_manager in scores:
        for player in scores[real_manager]['players']:
            # Initialize counters for simulated head-to-head comparisons
            num_simulated_games = 0
            num_wins = 0  # Net wins: +1 when player adds a win, -1 when replacement would win instead
            player_score = scores[real_manager]['players'][player]

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

            ffWAR_position[player] = {
                'ffWAR': ffWAR_score,
                'manager': real_manager,
                'position': position
            }
    
    return ffWAR_position


load_or_update_ffWAR_cache()