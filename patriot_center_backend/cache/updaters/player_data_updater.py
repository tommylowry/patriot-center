"""Utilities to build and maintain the ffWAR cache for Patriot Center.

This module:
- Loads supporting caches at import time (replacement scores and starters).
- Determines the current fantasy season/week.
- Loads an ffWAR cache JSON file and incrementally updates it by year/week.
- Persists the updated cache back to disk.

Algorithm summary:
- For each unprocessed week, derive per-position player scores.
- Simulate hypothetical matchups replacing each player with a positional
    replacement average.
- ffWAR = (net simulated wins difference) / (total simulations), rounded to
    3 decimals.
"""

import logging
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters._base import (
    get_player_info_and_score,
)
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
    get_roster_ids,
)

logger = logging.getLogger(__name__)


def update_player_data_cache(
    year: int, week: int
) -> None:
    """Incrementally updates the ffWAR cache JSON file by year/week.

    - Dynamically determines the current season and week
    according to Sleeper API/util logic.
    - Processes all years configured for leagues;
    this drives which seasons we consider for updates.
    - Reads progress markers from the cache to
    support incremental updates and resumability.
    - Skips years that are already fully processed
    based on the last recorded season.
    - If the cache is already up-to-date for
    the current season and week, stops processing.
    - Determines the range of weeks to update.
    - Fetches and updates only the missing weeks for the year.
    - Saves the updated cache to the file.
    - Reloads to remove the metadata fields.

    Args:
        year: The current season
        week: The current week
    """
    player_data_cache = CACHE_MANAGER.get_player_data_cache()

    if str(year) not in player_data_cache:
        player_data_cache[str(year)] = {}

    # Fetch ffWAR for the week.
    player_data_cache[str(year)][str(week)] = _fetch_ffwar(
        year, week
    )


def _fetch_ffwar(
    season: int, week: int
) -> dict[str, dict[str, Any]]:
    """Fetch and process the ffWAR data for a given week.

    Output is sorted by "ffWAR" in descending order then by "name".

    Args:
        season: The NFL season year (e.g., 2024).
        week: The week number (1-17).

    Returns:
        dict[str, dict[str, Any]]: A dictionary containing the ffWAR data
            for the given week.
    """
    starters_cache = CACHE_MANAGER.get_starters_cache()

    weekly_data = starters_cache[str(season)][str(week)]

    players = {"QB": {}, "RB": {}, "WR": {}, "TE": {}, "K": {}, "DEF": {}}

    for manager in weekly_data:
        for position in players:
            old_players_position = players[position]
            old_players_position[manager] = {
                "total_points": weekly_data[manager]["Total_Points"],
                "players": {},
            }
            players[position] = old_players_position

        for player in weekly_data[manager]:
            if player == "Total_Points":
                continue

            position = weekly_data[manager][player]['position']
            players[position][manager]['players'][player] = (
                weekly_data[manager][player]['points']
            )

    ffwar_results = {}
    all_player_scores = _get_all_player_scores(season, week)
    all_rostered_players = _get_all_rostered_players(season, week)

    for position in players:
        calculated_ffwar = _calculate_ffwar_position(
            players[position],
            season,
            week,
            position,
            all_player_scores[position],
            all_rostered_players,
        )
        if not calculated_ffwar:
            continue

        for player_id in calculated_ffwar:
            ffwar_results[player_id] = calculated_ffwar[player_id]

    # sort ffwar_position by ffWAR descending, then by name ascending
    ffwar_results = dict(
        sorted(
            ffwar_results.items(),
            key=lambda item: (-item[1]["ffWAR"], item[1]["name"]),
        )
    )

    return ffwar_results


def _calculate_ffwar_position(
    scores: dict[str, dict[str, Any]],
    season: int,
    week: int,
    position: str,
    all_player_scores: dict[str, dict[str, float | str]],
    all_rostered_players: dict[str, list[str]],
) -> dict[str, dict[str, Any]]:
    """Calculate fantasy football wins above replacement (ffWAR) for a position.

    This function takes in scores for all managers at a given position and week,
    and uses them to simulate head-to-head matchups to compute ffWAR for each
    player.

    - For each player, the function calculates the number of wins they
    contribute to their team, and subtracts the number of wins their
    replacement-level player would contribute instead.
    - The final ffWAR score is the win rate differential, scaled down by 1/3 in
    the playoffs.

    Args:
        scores: Scores for all managers at this position and week.
        season: The current season.
        week: The current week.
        position: The position to calculate ffWAR for.
        all_player_scores: Scores for all players at this position.
        all_rostered_players: Rostered players for each manager.

    Returns:
        A dictionary of ffWAR scores for each player at this position.
    """
    replacement_scores_cache = CACHE_MANAGER.get_replacement_score_cache()

    # Get the 3-year rolling average replacement score for this position
    key = f"{position}_3yr_avg"
    replacement_average = replacement_scores_cache[str(season)][str(week)][key]

    # Calculate the average score across all players at this position this week
    # This helps normalize scores when simulating replacement scenarios
    num_players = 0
    total_position_score = 0.0
    for manager in scores:
        num_players += len(scores[manager]["players"])
        for player in scores[manager]["players"]:
            total_position_score += scores[manager]["players"][player]

    if num_players == 0:
        return {}  # No players at this position this week

    average_player_score_this_week = total_position_score / num_players

    # Pre-compute normalized scores for each manager
    # These values are used in the simulation to isolate positional impact
    for manager in scores:
        # Calculate this manager's average score at this position
        player_total_for_manager = 0.0
        for player in scores[manager]["players"]:
            player_total_for_manager += scores[manager]["players"][player]

        # If no players at this position, set average to 0
        if len(scores[manager]["players"]) == 0:
            player_average_for_manager = 0
        else:
            player_average_for_manager = player_total_for_manager / len(
                scores[manager]["players"]
            )

        # Store manager's total points minus their positional contribution
        # This represents the manager's "baseline" without this position's
        #   impact
        scores[manager]["total_minus_position"] = (
            scores[manager]["total_points"] - player_average_for_manager
        )

        # Store normalized weighted score (baseline + league average at
        #   position)
        # Used as opponent's score in simulations
        scores[manager]["weighted_total_score"] = (
            scores[manager]["total_points"]
            - player_average_for_manager
            + average_player_score_this_week
        )

    # Simulate head-to-head matchups to compute ffWAR for each player
    ffwar_position = {}

    for player_id in all_player_scores:
        # Player's Full Name
        player = all_player_scores[player_id]["name"]

        # Determine if this player is rostered and started, and by whom
        player_data_manager_value = None
        started = False
        for manager in all_rostered_players:
            if player_id in all_rostered_players[manager]:
                player_data_manager_value = manager

                # Some managers may roster but not count in the scores if they
                # didn't play in the playoffs
                if player in scores.get(manager, {}).get("players", {}):
                    started = True
                break

        player_score = all_player_scores[player_id]["score"]

        player_data = {
            "name": player,
            "score": all_player_scores[player_id]["score"],
            "ffWAR": 0.0,
            "position": position,
            "manager": player_data_manager_value,
            "started": started,
        }

        # Initialize counters for simulated head-to-head comparisons
        num_simulated_games = 0

        # Net wins: +1 when player adds a win, -1 when replacement
        # would win instead
        num_wins = 0

        # Simulate all possible manager pairings with this player
        for manager_playing in scores:
            for manager_opposing in scores:
                if manager_playing == manager_opposing:
                    continue  # Skip self-matchups

                # Opponent's normalized score (baseline + position average)
                simulated_opponent_score = (
                    scores[manager_opposing]['weighted_total_score']
                )

                # Manager's score WITH this player at this position
                simulated_player_score = (
                    scores[manager_playing]["total_minus_position"]
                    + player_score
                )

                # Manager's score with REPLACEMENT-level player at this position
                simulated_replacement_score = (
                    scores[manager_playing]["total_minus_position"]
                    + replacement_average
                )

                # Case 1: Player wins but replacement would lose (player adds a
                #  win)
                if (
                    simulated_player_score > simulated_opponent_score
                    and simulated_replacement_score < simulated_opponent_score
                ):
                    num_wins += 1

                # Case 2: Player loses but replacement would win (player costs
                # a win)
                if (
                    simulated_player_score < simulated_opponent_score
                    and simulated_replacement_score > simulated_opponent_score
                ):
                    num_wins -= 1

                # Case 3 & 4: Both win or both lose (no impact on outcome,
                # ffWAR = 0 contribution)
                num_simulated_games += 1

        # Calculate final ffWAR score as win rate differential
        if num_simulated_games == 0:
            ffwar_score = 0.0
        else:
            ffwar_score = round(num_wins / num_simulated_games, 3)

            # Playoff adjustment: scale down by 1/3 since only 4 of 12 teams
            #   play each week
            # 2020 and earlier: playoffs start week 14
            # 2021 and later: playoffs start week 15
            if (season <= 2020 and week >= 14) or (
                season >= 2021 and week >= 15
            ):
                ffwar_score = round(ffwar_score / 3, 3)

        player_data["ffWAR"] = ffwar_score

        ffwar_position[player_id] = player_data

    return ffwar_position


def _get_all_player_scores(
    year: int, week: int
) -> dict[str, dict[str, dict[str, float | str]]]:
    """Fetch and calculate fantasy scores for all NFL players in a given week.

    This function retrieves raw stats from the Sleeper API for the specified
    year and week, then calculates each player's fantasy score based on the
    league's scoring settings. Players are grouped by position for easier
    processing.

    Args:
        year (int): The NFL season year (e.g., 2024).
        week (int): The week number (1-17).

    Returns:
        dict: Nested dictionary with structure
        Position -> Player ID -> Score and Player Name:
        - Each position contains all players who played that week (gp > 0),
        with their calculated fantasy score and full name.

    Raises:
        Exception: If the Sleeper API call fails.

    Notes:
        - Players with gp (games played) = 0 are excluded.
        - TEAM_ entries are skipped (not real players).
        - Defense players with numeric IDs are excluded.
        - Handles edge case of traded in real life players with modified IDs.
    """
    # Fetch data from the Sleeper API for the given season and week
    week_data = fetch_sleeper_data(f"stats/nfl/regular/{year}/{week}")
    if not isinstance(week_data, dict):
        raise Exception(
            f"Could not fetch week data for season {year} week {week}"
        )

    league_settings = fetch_sleeper_data(f"league/{LEAGUE_IDS.get(year)}")
    if not isinstance(league_settings, dict):
        raise Exception(f"Could not fetch league settings for season {year}")

    scoring_settings = league_settings.get("scoring_settings")
    if not scoring_settings:
        raise Exception(f"Could not find scoring settings for season {year}")

    final_week_scores = {
        "QB": {},
        "RB": {},
        "WR": {},
        "TE": {},
        "K": {},
        "DEF": {},
    }

    for player_id in week_data:
        # "TEAM_*" is stats for an entire team, so skip it
        if "TEAM_" in player_id:
            continue

        apply, player_info, score, player_id_used = get_player_info_and_score(
            player_id, week_data, final_week_scores, scoring_settings
        )
        if apply:
            # Add the player's points to the appropriate position list
            final_week_scores[player_info["position"]][player_id_used] = {
                "score": score,
                "name": player_info["full_name"],
            }

    return final_week_scores


def _get_all_rostered_players(
    season: int, week: int
) -> dict[str, list[str]]:
    """Get all players rostered by each manager for a specific week's matchup.

    Fetches matchup data from the Sleeper API and maps each manager to their
    list of rostered players for that week. Handles a known historical data
    inconsistency in early 2019.

    - Uses deep copy to avoid mutating the input roster_ids.
    - Player IDs are strings from the Sleeper API.

    Args:
        season: The season year.
        week: The week number.

    Returns:
        dict: Mapping of manager names to lists of player IDs they rostered.

    Raises:
        Exception: If the Sleeper API call fails.
    """
    roster_ids = get_roster_ids(season, week)

    # Handle known issue with Tommy's roster ID in early 2019 weeks
    # In weeks 1-3 of 2019, Cody's roster should be attributed to Tommy
    if season == 2019 and week <= 3:
        for key in roster_ids:
            if roster_ids[key] == "Cody":
                roster_ids[key] = "Tommy"
                break

    matchup_data_response = fetch_sleeper_data(
        f"league/{LEAGUE_IDS[season]}/matchups/{week}"
    )
    if not isinstance(matchup_data_response, list):
        raise Exception(
            f"Could not fetch matchup data for season {season} week {week}"
        )

    rostered_players = {}
    for matchup in matchup_data_response:
        rostered_players[roster_ids[matchup['roster_id']]] = (
            matchup['players']
        )

    return rostered_players
