"""Summary exporter for manager metadata."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache.queries.head_to_head_queries import (
    get_head_to_head_details_from_cache,
)
from patriot_center_backend.cache.queries.manager_queries import (
    get_manager_years_active_from_cache,
)
from patriot_center_backend.cache.queries.matchup_queries import (
    get_matchup_details_from_cache,
    get_overall_data_details_from_cache,
)
from patriot_center_backend.cache.queries.ranking_queries import (
    get_ranking_details_from_cache,
)
from patriot_center_backend.cache.queries.transaction_queries import (
    get_transaction_details_from_cache,
)
from patriot_center_backend.cache.updaters._validators import (
    validate_manager_query,
)
from patriot_center_backend.utils.image_url_handler import get_image_url


def get_manager_summary(
    manager: str, year: str | None = None
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
    validate_manager_query(manager, year)

    return_dict = {
        "manager_name": manager,
        "image_url": get_image_url(manager),
        "years_active": get_manager_years_active_from_cache(manager),
        "matchup_data": get_matchup_details_from_cache(manager, year=year),
        "transactions": get_transaction_details_from_cache(manager, year=year),
        "overall_data": get_overall_data_details_from_cache(manager),
        "rankings": get_ranking_details_from_cache(manager, year=year),
        "head_to_head": get_head_to_head_details_from_cache(manager, year=year),
    }

    return deepcopy(return_dict)

get_manager_summary(manager="Jay")