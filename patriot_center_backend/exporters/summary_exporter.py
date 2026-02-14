"""Summary exporter for manager metadata."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache.queries.head_to_head_queries import (
    get_head_to_head_details_from_cache,
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
    if not manager.check_participation(year):
        raise ValueError(f"Manager {manager} is not active in {year}.")

    return_dict = {
        "manager_name": manager.real_name,
        "image_url": manager.image_url,
        "years_active": manager.get_years_active(),
        "matchup_data": get_overall_matchup_details(manager, year=year),
        "transactions": get_transaction_details_from_cache(manager, year=year),
        "overall_data": get_overall_data_details(manager),
        "rankings": get_ranking_details_from_cache(manager, year=year),
        "head_to_head": get_head_to_head_details_from_cache(manager, year=year),
    }

    return deepcopy(return_dict)
