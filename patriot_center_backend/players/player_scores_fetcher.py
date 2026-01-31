"""This module provides functions for fetching and processing player data."""

from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.players.player_data import get_player_info_and_score
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
    get_roster_ids,
)


def fetch_all_player_scores(
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
        Exception: If the Sleeper API call fails or if valid options cache is
            not found.

    Notes:
        - Players with gp (games played) = 0 are excluded.
        - TEAM_ entries are skipped (not real players).
        - Defense players with numeric IDs are excluded.
        - Handles edge case of traded in real life players with modified IDs.
    """
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    positions = (
        valid_options_cache
        .get(str(year), {})
        .get(str(week), {})
        .get("positions")
    )
    if not positions:
        raise Exception(
            f"Valid options not found for season {year} week {week}"
        )

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

    final_week_scores = {pos: {} for pos in positions}

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


def fetch_rostered_players(
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

def fetch_starters_by_position(
    year: int, week: int
) -> dict[str, dict[str, Any]]:
    """Fetch the starters for each position for a given week.

    Args:
        year (int): The NFL season year (e.g., 2024).
        week (int): The week number (1-17).

    Returns:
        A dictionary where keys are positions and values are dictionaries
        containing the total points and scores for each manager in list form.
    """
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()
    managers = valid_options_cache[str(year)][str(week)]["managers"]
    positions = valid_options_cache[str(year)][str(week)]["positions"]

    starters_cache = CACHE_MANAGER.get_starters_cache()
    weekly_starters = starters_cache[str(year)][str(week)]

    # Initialize scores with empty values from valid options
    scores = {}
    for position in positions:
        scores[position] = {
            "players": [],
            "scores": [],
            "managers": {
                manager: {
                    "total_points": 0, "scores": []
                } for manager in managers
            },
        }

    for manager in managers:
        for position in positions:
            scores[position]["managers"][manager]["total_points"] = (
                weekly_starters[manager]["Total_Points"]
            )

        for player in weekly_starters[manager]:
            if player == "Total_Points":
                continue
            position = weekly_starters[manager][player]["position"]
            scores[position]["players"].append(player)
            scores[position]["scores"].append(
                weekly_starters[manager][player]["points"]
            )
            scores[position]["managers"][manager]["scores"].append(
                weekly_starters[manager][player]["points"]
            )

    return scores
