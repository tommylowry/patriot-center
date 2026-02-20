"""Manager list exporter for manager metadata."""

import logging
from copy import deepcopy
from typing import Any

from patriot_center_backend.cache.queries.manager_queries import (
    get_manager_summary_from_cache,
)
from patriot_center_backend.cache.queries.ranking_queries import (
    get_ranking_details_from_cache,
)
from patriot_center_backend.models import Manager

logger = logging.getLogger(__name__)


def get_managers_list(active_only: bool) -> dict[str, Any]:
    """Get a list of all managers in the system.

    Args:
        active_only: If True, only return active managers.

    Returns:
        A dictionary containing a list of manager metadata.
        Each manager is represented as a dictionary with the following keys:
            name: The manager's name.
            image_url: The URL of the manager's image.
            years_active: A list of years the manager has been active.
            total_trades: The total number of trades the manager has made.
            wins: The total number of wins the manager has.
            losses: The total number of losses the manager has.
            ties: The total number of ties the manager has.
            win_percentage: The manager's win percentage.
            placements: A dictionary containing the number of
                first, second, and third place finishes the manager has.
            playoff_appearances: The number of times the manager has
                appeared in the playoffs.
            best_finish: The best finish the manager has achieved.
            average_points_for: The average number of points the manager
                gets for each win.
            total_adds: The total number of adds the manager has made.
            total_drops: The total number of drops the manager has made.
            is_active: If the manager is currently active.
            rankings: A dictionary containing the manager's rankings in
                different categories.
    """
    managers_list = []

    all_ranking_details: dict[Manager, dict[str, Any]] = (
        get_ranking_details_from_cache(active_only=active_only)
    )

    for manager_obj in all_ranking_details:
        # TODO: change to manager
        manager = manager_obj.real_name
        # END TODO
        manager_summary = get_manager_summary_from_cache(manager)

        ranking_details = all_ranking_details[manager_obj]

        manager_item = manager_obj.get_metadata()
        manager_item["years_active"] = manager_obj.get_years_active()

        matchup_data_summary = manager_obj.get_matchup_data_summary()
        if not matchup_data_summary:
            logger.warning(
                f"Manager {manager_obj.real_name} ({manager_obj!s}) "
                f"has no matchup data."
            )
            continue

        manager_item["wins"] = matchup_data_summary["wins"]
        manager_item["losses"] = matchup_data_summary["losses"]
        manager_item["ties"] = matchup_data_summary["ties"]
        manager_item["win_percentage"] = matchup_data_summary["win_percentage"]

        manager_item["total_trades"] = manager_summary["transactions"][
            "trades"
        ]["total"]

        placements = {"first_place": 0, "second_place": 0, "third_place": 0}

        playoff_appearances = ranking_details["values"]["playoffs"]
        best_finish = 4

        overall_data_placements = manager_summary["overall_data"]["placement"]

        for y in overall_data_placements:
            year_placement = overall_data_placements[y]

            if year_placement == 1:
                placements["first_place"] += 1
            if year_placement == 2:
                placements["second_place"] += 1
            if year_placement == 3:
                placements["third_place"] += 1
            if year_placement < best_finish:
                best_finish = year_placement

        if best_finish == 4:
            if playoff_appearances > 0:
                best_finish = "Playoffs"
            else:
                best_finish = "Never Made Playoffs"

        # determine how high or low they should go in the list
        weight = 0
        weight += placements["first_place"] * 10000
        weight += placements["second_place"] * 1000
        weight += placements["third_place"] * 100
        weight += playoff_appearances * 10
        weight += ranking_details["values"]["average_points_for"]
        manager_item["weight"] = weight

        manager_item["placements"] = deepcopy(placements)
        manager_item["playoff_appearances"] = ranking_details["values"][
            "playoffs"
        ]

        manager_item["best_finish"] = best_finish
        manager_item["average_points_for"] = ranking_details["values"][
            "average_points_for"
        ]

        manager_item["total_adds"] = manager_summary["transactions"]["adds"][
            "total"
        ]

        manager_item["total_drops"] = manager_summary["transactions"]["drops"][
            "total"
        ]

        manager_item["is_active"] = ranking_details["ranks"][
            "is_active_manager"
        ]

        rankings = {
            "win_percentage": ranking_details["ranks"]["win_percentage"],
            "average_points_for": (
                ranking_details["ranks"]["average_points_for"]
            ),
            "trades": ranking_details["ranks"]["trades"],
            "playoffs": ranking_details["ranks"]["playoffs"],
            "worst": ranking_details["ranks"]["worst"],
        }

        manager_item["rankings"] = deepcopy(rankings)

        managers_list.append(manager_item)

    return {"managers": managers_list}
