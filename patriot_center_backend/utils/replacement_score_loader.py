"""Replacement-score cache builder for Patriot Center.

Responsibilities:
- Maintain a JSON cache of per-week replacement-level scores by position.
- Backfill historical seasons and compute 3-year rolling averages keyed by bye
counts.
- Persist an incrementally updated cache to disk and expose it to callers.

Notes:
- Uses Sleeper API data (network I/O) via fetch_sleeper_data.
- Seed player metadata via load_player_ids to filter and position players.
- Current season/week is resolved at runtime and weeks are capped by era rules.
"""

import logging
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.utils.scoring import calculate_player_score
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
    get_current_season_and_week,
)

logger = logging.getLogger(__name__)


def update_replacement_score_cache() -> None:
    """Incrementally update the replacement score cache.

    Algorithm summary:
    - Dynamically determine the current season and week.
    - Process all years in LEAGUE_IDS with extra years for replacement score
        backfill.
    - Skip years that are already fully processed.
    - Fetch and update only the missing weeks for each year.
    - Compute the 3-year average if data from three years ago exists.
    - Update the metadata for the last updated season and week.
    - Save the updated cache to the file.
    - Reload to remove the metadata fields.

    Notes:
    - Uses Sleeper API data (network I/O) via fetch_sleeper_data.
    - Seed player metadata via load_player_ids to filter and position players.
    - Current season/week is resolved at runtime and weeks are capped by era
        rules.
    """
    replacement_score_cache = CACHE_MANAGER.get_replacement_score_cache(
        for_update=True
    )

    # Dynamically determine the current season and week
    current_season, current_week = get_current_season_and_week()
    if current_week > 18:
        current_week = 18  # Cap the current week at 18 (NFL's maximum)

    # Process all years in LEAGUE_IDS with extra years for replacement score
    years = list(LEAGUE_IDS.keys())
    first_year = min(years)
    # Add the three years prior to the first year in LEAGUE_IDS
    # for historical averages
    years.extend([first_year - 3, first_year - 2, first_year - 1])
    years = sorted(years)

    for year in years:
        # Get the last updated season and week from the cache
        last_updated_season = int(
            replacement_score_cache.get("Last_Updated_Season", 0)
        )
        last_updated_week = replacement_score_cache.get("Last_Updated_Week", 0)

        # Skip years that are already fully processed
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                # Reset the week if moving to a new year
                replacement_score_cache["Last_Updated_Week"] = 0

        # If the cache is already up-to-date for the
        # current season and week, stop processing
        if (
            last_updated_season == int(current_season)
            and last_updated_week == current_week
        ):
            break

        max_weeks = _get_max_weeks(year, int(current_season), current_week)

        # Determine the range of weeks to update
        if year in (int(current_season), last_updated_season):
            last_updated_week = replacement_score_cache.get(
                "Last_Updated_Week", 0
            )
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)

        if list(weeks_to_update) == []:
            # No new weeks to process
            continue

        logger.info(
            f"Updating replacement score cache for "
            f"season {year}, weeks: {list(weeks_to_update)}"
        )

        # Fetch and update only the missing weeks for the year
        for week in weeks_to_update:
            if str(year) not in replacement_score_cache:
                replacement_score_cache[str(year)] = {}

            # Fetch replacement scores for the week
            replacement_score_cache[str(year)][str(week)] = (
                _fetch_replacement_score_for_week(year, week)
            )

            # Compute the 3-year average if data from three years ago exists
            if str(year - 3) in replacement_score_cache:
                # Augment with bye-aware 3-year rolling averages
                replacement_score_cache[str(year)][str(week)] = (
                    _get_three_yr_avg(year, week)
                )

            # Update the metadata for the last updated season and week
            replacement_score_cache["Last_Updated_Season"] = str(year)
            replacement_score_cache["Last_Updated_Week"] = week

            logger.info(
                f"\tReplacement score cache updated "
                f"internally for season {year}, week {week}"
            )

    # Save the updated cache to the file
    CACHE_MANAGER.save_replacement_score_cache()

    # Reload to remove the metadata fields
    CACHE_MANAGER.get_replacement_score_cache(force_reload=True)


def _get_max_weeks(season: int, current_season: int, current_week: int) -> int:
    """Determine maximum playable weeks for a season.

    Rules:
    - Live season -> current_week.
    - 2020 and earlier -> 17 (legacy rule set).
    - Other seasons -> 18 (regular season boundary).

    Args:
        season: The season to determine the max weeks for.
        current_season: The current season.
        current_week: The current week.

    Returns:
        Max week to process for season.
    """
    if season == current_season:
        return current_week  # Use the current week for the current season
    elif season <= 2020:
        return 17  # Cap at 17 weeks for seasons 2020 and earlier
    else:
        return 18  # Cap at 18 weeks for other seasons


def _fetch_replacement_score_for_week(season: int, week: int) -> dict[str, Any]:
    """Derive positional replacement thresholds for a week.

    Thresholds (descending rank):
        QB13, RB31, WR31, TE13

    Returns:
        dict: {QB, RB, WR, TE, byes}
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    # Fetch data from the Sleeper API for the given season and week
    week_data = fetch_sleeper_data(f"stats/nfl/regular/{season}/{week}")
    if not isinstance(week_data, dict):
        raise ValueError(
            f"Sleeper API call failed for season {season}, week {week}"
        )

    yearly_scoring_settings = {}
    for yr in range(season, season + 4):
        if yr not in LEAGUE_IDS:
            continue
        scoring_settings = fetch_sleeper_data(f"league/{LEAGUE_IDS[yr]}")
        if not isinstance(scoring_settings, dict):
            raise ValueError(
                f"Sleeper API call failed to retrieve "
                f"scoring settings for year {yr}"
            )
        yearly_scoring_settings[yr] = scoring_settings["scoring_settings"]

    # Initialize the byes counter
    final_week_scores = {
        "byes": 32
    }
    for yr in yearly_scoring_settings:

        week_scores = {
            "QB": [],   # List of QB scores for the week
            "RB": [],   # List of RB scores for the week
            "WR": [],   # List of WR scores for the week
            "TE": [],   # List of TE scores for the week
            "K": [],    # List of K scores for the week
            "DEF": [],  # List of DEF scores for the week
        }

        for player_id in week_data:

            if "TEAM_" in player_id:
                if final_week_scores.get("byes") is None:
                    # TEAM_ entries represent real teams -> decrement byes
                    final_week_scores["byes"] -= 1
                continue

            if player_id not in player_ids_cache:
                only_numeric = ''.join(filter(str.isdigit, player_id))
                if only_numeric in player_ids_cache:
                    player_name = player_ids_cache[only_numeric]["full_name"]
                    print(f"Weird possibly traded player id encountered in replacement score calculation for season {season} week {week}, probably {player_name}, using {only_numeric} instead of {player_id}")
                    player_id = only_numeric
                else:
                    print("Unknown numeric player id encountered in replacement score calculation for:", player_id)
                    continue

            # Get player information from PLAYER_IDS
            player_info = player_ids_cache[player_id]

            # Check if player id is numeric
            if player_id.isnumeric() and player_info["position"] == "DEF":
                continue

            if player_info["position"] in week_scores:
                player_data = week_data[player_id]

                if "gp" not in player_data or player_data["gp"] == 0.0:
                    continue

                player_score = calculate_player_score(player_data, yearly_scoring_settings[yr])
                # Add the player's points to the appropriate position list
                week_scores[player_info["position"]].append(player_score)

        # Sort scores for each position in descending order
        for position in week_scores:
            week_scores[position].sort(reverse=True)

        # Determine the replacement scores for each position
        final_week_scores[f"{yr}_scoring"] = {}
        final_week_scores[f"{yr}_scoring"]["QB"] = week_scores["QB"][12]   # 13th QB
        final_week_scores[f"{yr}_scoring"]["RB"] = week_scores["RB"][30]   # 31st RB
        final_week_scores[f"{yr}_scoring"]["WR"] = week_scores["WR"][30]   # 31st WR
        final_week_scores[f"{yr}_scoring"]["TE"] = week_scores["TE"][12]   # 13th TE
        final_week_scores[f"{yr}_scoring"]["K"] = week_scores["K"][12]     # 13th K
        final_week_scores[f"{yr}_scoring"]["DEF"] = week_scores["DEF"][12] # 13th DEF

        # Add the final number of byes to the scores
        final_week_scores["byes"] = byes

    return final_week_scores

def _get_three_yr_avg(season, week):
    """
    Compute bye-aware 3-year rolling averages for replacement scores.

    Monotonicity:
        More byes => scores must not decrease (enforced by backward pass).
    """
    replacement_score_cache = CACHE_MANAGER.get_replacement_score_cache()

    # Get the current week's scores and the number of byes
    current_week_scores = replacement_score_cache[str(season)][str(week)]
    byes = current_week_scores["byes"]

    # Initialize dictionaries to store scores and averages for each position
    three_yr_season_scores = {}
    three_yr_season_average = {}

    # Prepare structures for each position (QB, RB, WR, TE)
    for current_week_position in current_week_scores[f"{season}_scoring"]:
        if current_week_position == "byes":
            continue  # Skip the "byes" field
        three_yr_season_scores[current_week_position] = {}
        three_yr_season_average[current_week_position] = {}

    # Iterate through the past three years (and the current year)
    for past_year in [season, season - 1, season - 2, season - 3]:
        # Determine the weeks to consider for the past year
        weeks = range(1, 18 if past_year <= 2020 else 19)

        # For the current season, only consider up to the current week
        if past_year == season:
            # Only include weeks completed this season
            weeks = range(1, week + 1)

        # For the season three years ago, only consider from the current week onward
        if past_year == season - 3:
            # Mirror future-season portion to balance sample across bye distributions
            weeks = range(week, 18 if past_year <= 2020 else 19)

        # Process each week in the determined range
        for w in weeks:
            # Skip if the data for the past year or week is missing
            if str(past_year) not in replacement_score_cache or str(w) not in replacement_score_cache[str(past_year)]:
                continue

            if w == week and past_year == season - 3:
                # Skip the current week of the season three years ago as this week makes it 3 years
                continue

            # Get the number of byes for the past week
            past_byes = replacement_score_cache[str(past_year)][str(w)]["byes"]

            # Process scores for each position (QB, RB, WR, TE)
            for past_position in three_yr_season_scores:
                # Get the score for the position in the past week
                past_score = replacement_score_cache[str(past_year)][str(w)][f"{season}_scoring"][past_position]

                # Initialize the list for the bye count if it doesn't exist
                if past_byes not in three_yr_season_scores[past_position]:
                    three_yr_season_scores[past_position][past_byes] = []

                # Append the score to the list for the corresponding bye count
                three_yr_season_scores[past_position][past_byes].append(past_score)

    # Compute the average replacement scores for each position and bye count
    for past_position in three_yr_season_scores:
        for past_byes in three_yr_season_scores[past_position]:
            # Calculate the average score for the position and bye count
            avg = sum(three_yr_season_scores[past_position][past_byes]) / len(
                three_yr_season_scores[past_position][past_byes]
            )
            three_yr_season_average[past_position][past_byes] = avg

    # Ensure monotonicity: more byes should not lead to lower replacement scores
    # This ensures that the replacement scores are non-decreasing as the number of byes increases
    list_of_byes = sorted(three_yr_season_average["QB"].keys())  # Use QB as a reference for bye counts
    for past_position in three_yr_season_average:
        for i in range(len(list_of_byes) - 1, 0, -1):
            # If the score for a higher bye count is greater than the score for a lower bye count,
            # adjust the lower bye count's score to ensure monotonicity
            if three_yr_season_average[past_position][list_of_byes[i]] > three_yr_season_average[past_position][
                list_of_byes[i - 1]
            ]:
                three_yr_season_average[past_position][list_of_byes[i - 1]] = three_yr_season_average[past_position][
                    list_of_byes[i]
                ]

    # Add the three-year averages to the current week's scores
    for past_position in three_yr_season_average:
        new_key = f"{past_position}_3yr_avg"
        current_week_scores[new_key] = three_yr_season_average[past_position][byes]

    # Return the updated current week's scores with three-year averages added
    return current_week_scores

_fetch_replacement_score_for_week(2019, 11)