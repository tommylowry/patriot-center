"""Summary exporter for manager metadata."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache.queries.head_to_head_queries import (
    get_head_to_head_details_for_opponents,
)
from patriot_center_backend.cache.queries.matchup_queries import (
    get_overall_data_details,
    get_overall_matchup_details,
)
from patriot_center_backend.cache.queries.ranking_queries import (
    get_ranking_details_from_cache,
)
from patriot_center_backend.cache.queries.transaction_queries import (
    get_transaction_details_from_cache,
)
from patriot_center_backend.models import Manager


def get_manager_summary(
    manager: Manager, year: str | None = None
) -> dict[str, Any]:
    """Get comprehensive manager summary.

    Includes:
    - Manager name and image URL
    - List of years active
    - Matchup data (wins, losses, ties, win percentage,
        average points for/against)
    - Transaction data (adds, drops, trades)
    - Overall data (placement counts, playoff appearances,
        biggest blowout win/loss)
    - Rankings (win percentage, average points for, trades, playoffs,
        worst finish)
    - Head-to-head data (wins, losses, ties, points for/against,
        num trades between)

    Args:
        manager: Manager name
        year: Season year (optional - defaults to all-time)

    Returns:
        dictionary with all manager summary data
    """
    if not manager.participated(year):
        raise ValueError(f"Manager {manager} is not active in {year}.")

    all_ranking_details = get_ranking_details_from_cache(year=year)
    return_dict = {
        "metadata": manager.get_metadata(),
        "is_active": manager.is_active(),
        "years_active": manager.get_years_active(),
        "matchup_data": get_overall_matchup_details(manager, year=year),
        "transactions": get_transaction_details_from_cache(manager, year=year),
        "overall_data": get_overall_data_details(manager),
        "rankings": all_ranking_details[manager],
        "head_to_head": get_head_to_head_details_for_opponents(
            manager, year=year
        ),
    }

    placements = manager.get_playoff_placements()
    playoff_appearances = manager.get_playoff_appearances_list()
    if not placements:
        if not playoff_appearances:
            return_dict["best_finish"] = "Never Made Playoffs"
        else:
            return_dict["best_finish"] = "Playoffs"
    else:
        return_dict["best_finish"] = max(placements.values())

    # determine how high or low they should go in the list
    weight = 0
    weight += placements["first_place"] * 10000
    weight += placements["second_place"] * 1000
    weight += placements["third_place"] * 100
    weight += len(playoff_appearances) * 10
    weight += (
        return_dict
        .get("rankings", {})
        .get("values", {})
        .get("average_points_for", 0.0)
    )
    return_dict["weight"] = weight

    return deepcopy(return_dict)


def get_manager_summaries(
    active_only: bool = True, year: str | None = None
) -> list[dict[str, Any]]:
    """Get comprehensive manager summary.

    Args:
        active_only: If True, only return active managers.
        year: Season year (optional - defaults to all-time)

    Returns:
        List of dictionaries with manager summary data
    """
    managers = Manager.get_managers(year=year, active_only=active_only)

    summaries = []
    for manager in managers:
        summaries.append(get_manager_summary(manager, year))

    return summaries
