"""Cache query helpers for reading matchup related manager metadata."""

import logging
from copy import deepcopy
from decimal import Decimal
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.managers.formatters import get_matchup_card

logger = logging.getLogger(__name__)


def get_matchup_details_from_cache(
    manager: str, year: str | None = None
) -> dict[str, dict[str, int | float]]:
    """Get comprehensive matchup statistics broken down by season state.

    Extracts wins, losses, ties, win percentage, and point averages for:
    - Overall (all matchups)
    - Regular season only
    - Playoffs only

    Handles cases where manager has no playoff appearances.

    Args:
        manager: Manager name
        year: Season year (optional - defaults to all-time stats if None)

    Returns:
        Dictionary with matchup stats for overall, regular_season, and playoffs
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    matchup_data = {"overall": {}, "regular_season": {}, "playoffs": {}}

    # Get all-time stats by default, or single season stats if year specified
    cached_matchup_data = deepcopy(
        manager_cache[manager]["summary"]["matchup_data"]
    )
    if year:
        cached_matchup_data = deepcopy(
            manager_cache[manager]["years"][year]["summary"]["matchup_data"]
        )

    season_states = ["overall", "regular_season"]

    # Check if manager has playoff appearances
    playoff_appearances = (
        manager_cache
        .get(manager, {})
        .get("summary", {})
        .get("overall_data", {})
        .get("playoff_appearances", [])
    )

    has_playoff_data = (
        len(playoff_appearances) > 0
        and (not year or year in playoff_appearances)
    )

    if has_playoff_data:
        season_states.append("playoffs")

    else:  # Manager has no playoff appearances
        matchup_data["playoffs"] = {
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "win_percentage": 0.0,
            "average_points_for": 0.0,
            "average_points_against": 0.0,
            "average_point_differential": 0.0,
        }

    for season_state in season_states:
        # Extract win-loss-tie record
        num_wins = cached_matchup_data[season_state]["wins"]["total"]
        num_losses = cached_matchup_data[season_state]["losses"]["total"]
        num_ties = cached_matchup_data[season_state]["ties"]["total"]

        matchup_data[season_state]["wins"] = num_wins
        matchup_data[season_state]["losses"] = num_losses
        matchup_data[season_state]["ties"] = num_ties

        # Calculate win percentage (rounded to 1 decimal place)
        num_matchups = num_wins + num_losses + num_ties

        win_percentage = 0.0
        if num_matchups != 0:
            win_percentage = (num_wins / num_matchups) * 100
            win_percentage = float(
                Decimal(win_percentage).quantize(Decimal("0.1"))
            )

        matchup_data[season_state]["win_percentage"] = win_percentage

        # Calculate point averages (rounded to 2 decimal places)
        total_points_for = (
            cached_matchup_data
            .get(season_state, {})
            .get("points_for", {})
            .get("total", 0.0)
        )
        total_points_against = (
            cached_matchup_data
            .get(season_state, {})
            .get("points_against", {})
            .get("total", 0.0)
        )

        point_diff = total_points_for - total_points_against
        total_point_differential = float(
            Decimal(point_diff).quantize(Decimal("0.01"))
        )

        if num_matchups != 0:
            avg_pf = total_points_for / num_matchups
            avg_pf = float(Decimal(avg_pf).quantize(Decimal("0.01")))

            avg_pa = total_points_against / num_matchups
            avg_pa = float(Decimal(avg_pa).quantize(Decimal("0.01")))

            avg_pd = total_point_differential / num_matchups
            avg_pd = float(Decimal(avg_pd).quantize(Decimal("0.01")))

        else:  # No matchups
            avg_pf = 0.0
            avg_pa = 0.0
            avg_pd = 0.0

        matchup_data[season_state]["average_points_for"] = avg_pf
        matchup_data[season_state]["average_points_against"] = avg_pa
        matchup_data[season_state]["average_point_differential"] = avg_pd

    return deepcopy(matchup_data)


def get_overall_data_details_from_cache(
    manager: str
) -> dict[str, int | list[Any]]:
    """Get career achievements with playoff appearances & season placements.

    Args:
        manager: Manager name

    Returns:
        Dictionary with playoff_appearances count and list of placements by year
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    cached_overall_data = deepcopy(
        manager_cache[manager]["summary"]["overall_data"]
    )

    overall_data: dict[str, int | list[Any]] = {
        "playoff_appearances": len(
            cached_overall_data.get("playoff_appearances", [])
        ),
    }

    # ----- Other Overall Data -----
    placements = []
    for year in cached_overall_data.get("placement", {}):
        week = "17"
        if int(year) <= 2020:
            week = "16"

        opponent = (
            manager_cache
            .get(manager, {})
            .get("years", {})
            .get(year, {})
            .get("weeks", {})
            .get(week, {})
            .get("matchup_data", {})
            .get("opponent_manager", "")
        )

        matchup_card = {}
        if opponent == "":
            logger.warning(
                f"Unable to retreive opponent for "
                f"matchup card for year {year} week {week}"
            )
        else:
            matchup_card = get_matchup_card(
                manager, opponent, year, week
            )

        placement_item = {
            "year": year,
            "placement": cached_overall_data["placement"][year],
            "matchup_card": matchup_card,
        }
        placements.append(placement_item)

    overall_data["placements"] = placements

    return deepcopy(overall_data)
