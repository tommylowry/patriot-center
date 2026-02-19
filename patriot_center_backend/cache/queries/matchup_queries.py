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
    matchup_data = {
        "overall": manager.get_matchup_data_summary(year=year),
        "regular_season": manager.get_matchup_data_summary(year=year),
        "playoffs": manager.get_matchup_data_summary(year=year),
    }
    if not matchup_data["playoffs"]:
        del matchup_data["playoffs"]
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
