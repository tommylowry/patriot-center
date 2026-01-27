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
from patriot_center_backend.cache.updaters._base import (
    get_max_weeks,
    get_player_info_and_score,
)
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
)

logger = logging.getLogger(__name__)


def update_replacement_score_cache(year: int, week: int) -> None:
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

    Args:
        year: The current season.
        week: The current week.
    """
    replacement_score_cache = CACHE_MANAGER.get_replacement_score_cache()

    if not replacement_score_cache:
        _backfill_three_years(year)

    if str(year) not in replacement_score_cache:
        replacement_score_cache[str(year)] = {}

    # Fetch replacement scores for the week
    replacement_data = _fetch_replacement_score_for_week(year, week)
    if not replacement_data:
        return

    # Update the cache
    replacement_score_cache[str(year)][str(week)] = (
        _fetch_replacement_score_for_week(year, week)
    )

    # Compute the 3-year average if data from three years ago exists
    if str(year - 3) in replacement_score_cache:
        # Augment with bye-aware 3-year rolling averages
        replacement_score_cache[str(year)][str(week)] = _get_three_yr_avg(
            year, week
        )

    logger.info(
        f"\tSeason {year}, Week {week}: Replacement Score Cache Updated."
    )


def _backfill_three_years(year: int) -> None:
    """Backfill the initial three years of replacement scores.

    Args:
        year: The year to backfill.
    """
    replacement_score_cache = CACHE_MANAGER.get_replacement_score_cache()

    logger.info(
        f"Starting backfill of replacement score cache for season {year}"
    )

    for backfill_year in range(year - 3, year):
        if str(backfill_year) not in replacement_score_cache:
            replacement_score_cache[str(backfill_year)] = {}

        max_weeks = get_max_weeks(backfill_year, true_max=True)

        # Determine the range of weeks to update
        weeks_to_update = range(1, max_weeks + 1)

        logger.info(
            f"Backfilling replacement score cache with "
            f"season {backfill_year}, weeks: {list(weeks_to_update)}"
        )

        for week in weeks_to_update:
            # Update the cache
            update_replacement_score_cache(backfill_year, week)


def _fetch_replacement_score_for_week(season: int, week: int) -> dict[str, Any]:
    """Fetches replacement scores for the given season and week.

    The replacement scores are determined by sorting the fantasy scores
    for each position in descending order and taking the 13th score for
    QB, TE, K, and DEF, and the 31st score for RB and WR.

    Args:
        season: The season to fetch replacement scores for.
        week: The week to fetch replacement scores for.

    Returns:
        A dictionary with the replacement scores for each position given
            each fantasy year's scoring settings along with the number of byes
            in the week.

    Raises:
        ValueError: If the Sleeper API call fails to retrieve the necessary
            data.
    """
    # Fetch data from the Sleeper API for the given season and week
    week_data = fetch_sleeper_data(f"stats/nfl/regular/{season}/{week}")
    if not isinstance(week_data, dict):
        raise ValueError(
            f"Sleeper API call failed for season {season}, week {week}"
        )

    if not week_data:
        logger.warning(
            f"No data found for season {season}, week {week}. "
            "Returning empty replacement score."
        )
        return {}

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
    final_week_scores: dict[str, Any] = {"byes": 32}
    first = True
    for yr in yearly_scoring_settings:
        week_scores = {
            "QB": [],  # List of QB scores for the week
            "RB": [],  # List of RB scores for the week
            "WR": [],  # List of WR scores for the week
            "TE": [],  # List of TE scores for the week
            "K": [],  # List of K scores for the week
            "DEF": [],  # List of DEF scores for the week
        }

        for player_id in week_data:
            if "TEAM_" in player_id:
                if first:
                    # TEAM_ entries represent real teams -> decrement byes
                    final_week_scores["byes"] -= 1
                continue

            apply, player_info, score, _ = get_player_info_and_score(
                player_id,
                week_data,
                week_scores,
                yearly_scoring_settings[yr],
            )
            if apply:
                # Add the player's points to the appropriate position list
                week_scores[player_info["position"]].append(score)

        # Set first to false after first iteration
        # since we have the number of byes
        first = False

        # Sort scores for each position in descending order
        for position in week_scores:
            week_scores[position].sort(reverse=True)

        # Determine the replacement scores for each position
        final_week_scores[f"{yr}_scoring"] = {
            "QB": week_scores["QB"][12],  # 13th QB
            "RB": week_scores["RB"][30],  # 31st RB
            "WR": week_scores["WR"][30],  # 31st WR
            "TE": week_scores["TE"][12],  # 13th TE
            "K": week_scores["K"][12],  # 13th K
            "DEF": week_scores["DEF"][12],  # 13th DEF
        }

    return final_week_scores


def _get_three_yr_avg(season: int, week: int) -> dict[str, Any]:
    """Compute the three-year average replacement scores for each position.

    - Iterates through the past three years (and the current year)
    - Determines the weeks to consider for the past year
    - Processes each week in the determined range
    - Computes the average replacement scores for each position and bye
    count
    - Ensures monotonicity: more byes should not lead to lower replacement
    scores

    Parameters:
        season: The current season
        week: The current week

    Returns:
        The updated current week's scores with three-year averages added
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
        if str(past_year) not in replacement_score_cache:
            continue

        # Determine the weeks to consider for the past year
        weeks = range(1, 18 if past_year <= 2020 else 19)

        # For the current season, only consider up to the current week
        if past_year == season:
            # Only include weeks completed this season
            weeks = range(1, week + 1)

        # For the season three years ago, only consider
        # from the current week onward
        if past_year == season - 3:
            # Mirror future-season portion to balance
            # sample across bye distributions
            weeks = range(week, 18 if past_year <= 2020 else 19)

        # Process each week in the determined range
        for w in weeks:
            # Skip if the data for the past year or week is missing
            if str(w) not in replacement_score_cache[str(past_year)]:
                continue

            if w == week and past_year == season - 3:
                # Skip the current week of the season three years
                # ago as this week makes it 3 years
                continue

            week_data = replacement_score_cache[str(past_year)][str(w)]

            # Get the number of byes for the past week
            past_byes = week_data["byes"]

            # Process scores for each position (QB, RB, WR, TE)
            for past_position in three_yr_season_scores:
                # Get the score for the position in the past week
                past_score = week_data[f"{season}_scoring"][past_position]

                past_position_scores = three_yr_season_scores[past_position]

                # Initialize the list for the bye count if it doesn't exist
                if past_byes not in past_position_scores:
                    past_position_scores[past_byes] = []

                # Append the score to the list for the corresponding bye count
                past_position_scores[past_byes].append(past_score)

    # Compute the average replacement scores for each position and bye count
    for past_position in three_yr_season_scores:
        for past_byes in three_yr_season_scores[past_position]:
            # Calculate the average score for the position and bye count
            avg = sum(three_yr_season_scores[past_position][past_byes]) / len(
                three_yr_season_scores[past_position][past_byes]
            )
            three_yr_season_average[past_position][past_byes] = avg

    # Ensure monotonicity: more byes should not lead to lower replacement scores
    # This ensures that the replacement scores are non-decreasing as the
    #   number of byes increases

    # Use QB as a reference for bye counts
    list_of_byes = sorted(three_yr_season_average["QB"].keys())
    for past_position in three_yr_season_average:
        position_dict = three_yr_season_average[past_position]
        for i in range(len(list_of_byes) - 1, 0, -1):
            more_byes = list_of_byes[i]
            less_byes = list_of_byes[i - 1]

            # If the score for a higher bye count is greater than the score for
            # a lower bye count, adjust the lower bye count's score to ensure
            # monotonicity
            if position_dict[more_byes] > position_dict[less_byes]:
                position_dict[less_byes] = position_dict[more_byes]

    # Add the three-year averages to the current week's scores
    for past_position in three_yr_season_average:
        new_key = f"{past_position}_3yr_avg"
        current_week_scores[new_key] = (
            three_yr_season_average[past_position][byes]
        )

    # Return the updated current week's scores with three-year averages added
    return current_week_scores
