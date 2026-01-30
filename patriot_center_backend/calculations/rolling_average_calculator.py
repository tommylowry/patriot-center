"""Calculates the three-year average replacement scores for each position."""

from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER


def calculate_three_year_averages(season: int, week: int) -> dict[str, Any]:
    """Compute the three-year average replacement scores for each position.

    - Iterates through the past three years (and the current year)
    - Determines the weeks to consider for the past year
    - Processes each week in the determined range
    - Computes the average replacement scores for each position and bye
    count
    - Ensures monotonicity: more byes should not lead to lower replacement
    scores

    Args:
        season: The current season.
        week: The current week.

    Returns:
        The updated current week's scores with three-year averages added.
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

    # Enforce monotonicity: more byes should not lead to lower replacement
    # scores
    _enforce_monotonicity(three_yr_season_average)

    # Add the three-year averages to the current week's scores
    for past_position in three_yr_season_average:
        new_key = f"{past_position}_3yr_avg"
        current_week_scores[new_key] = (
            three_yr_season_average[past_position][byes]
        )

    # Return the updated current week's scores with three-year averages added
    return current_week_scores


def _enforce_monotonicity(averages: dict[str, dict[str, float]]) -> None:
    """Enforce monotonicity by ensuring lower bye counts have lower scores.

    Args:
        averages: A dictionary of position averages keyed by bye count.
    """
    # Ensure monotonicity: more byes should not lead to lower replacement scores
    # This ensures that the replacement scores are non-decreasing as the
    #   number of byes increases

    # Use QB as a reference for bye counts
    list_of_byes = sorted(averages["QB"].keys())
    for position in averages:
        position_dict = averages[position]
        for i in range(len(list_of_byes) - 1, 0, -1):
            more_byes = list_of_byes[i]
            less_byes = list_of_byes[i - 1]

            # If the score for a higher bye count is greater than the score for
            # a lower bye count, adjust the lower bye count's score to ensure
            # monotonicity
            if position_dict[more_byes] > position_dict[less_byes]:
                position_dict[less_byes] = position_dict[more_byes]
