"""Cache query helpers for reading matchup related manager metadata."""

import logging
from copy import deepcopy
from typing import Any

from patriot_center_backend.models import Manager
from patriot_center_backend.utils.formatters import get_matchup_card

logger = logging.getLogger(__name__)


def get_overall_matchup_details(
    manager: Manager, year: str | None = None
) -> dict[str, dict[str, Any]]:
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
    regular_season_data = manager.get_matchup_data_summary(
        year=year, matchup_type="regular_season"
    )
    playoff_data = manager.get_matchup_data_summary(
        year=year, matchup_type="playoffs"
    )

    if not playoff_data:
        overall_data = deepcopy(regular_season_data)
        matchup_data = {"overall": overall_data, "regular_season": overall_data}
    else:
        overall_data = {}
        for key in regular_season_data:
            overall_data[key] = regular_season_data[key] + playoff_data[key]
        matchup_data = {
            "overall": overall_data,
            "regular_season": regular_season_data,
            "playoffs": playoff_data,
        }

    keys_to_remove = []
    for matchup_key, matchup_value in matchup_data.items():
        num_games = (
            matchup_value["wins"]
            + matchup_value["losses"]
            + matchup_value["ties"]
        )
        if num_games == 0:
            keys_to_remove.append(matchup_key)
            continue

        matchup_value["win_percentage"] = round(
            matchup_value["wins"] / num_games, 1
        )
        matchup_value["average_points_for"] = round(
            matchup_value["points_for"] / num_games, 2
        )
        matchup_value["average_points_against"] = round(
            matchup_value["points_against"] / num_games, 2
        )
        matchup_value["average_point_differential"] = round(
            matchup_value.pop("points_for")
            - matchup_value.pop("points_against"),
            2,
        )

    for key in keys_to_remove:
        matchup_data.pop(key)

    return matchup_data


def get_overall_data_details(manager: Manager) -> dict[str, Any]:
    """Get career achievements with playoff appearances & season placements.

    Args:
        manager: Manager name

    Returns:
        Dictionary with playoff_appearances count and list of placements by year
    """
    overall_data: dict[str, int | list[Any]] = {
        "playoff_appearances": len(manager.get_playoff_appearances_list()),
    }

    playoff_placements = manager.get_playoff_placements()

    # ----- Other Overall Data -----
    placements_list = []
    for year in playoff_placements:
        last_matchup = manager.get_last_matchup(year=year)

        opponent = last_matchup["opponent"]
        week = last_matchup["week"]

        matchup_card = get_matchup_card(manager, opponent, year, week)

        placement_item = {
            "year": year,
            "placement": playoff_placements[year],
            "matchup_card": matchup_card,
        }
        placements_list.append(placement_item)

    overall_data["placements"] = placements_list

    return deepcopy(overall_data)
