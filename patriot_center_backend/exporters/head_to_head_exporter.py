"""Head-to-head exporter for manager metadata."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache.queries.head_to_head_queries import (
    get_head_to_head_overall_from_cache,
)
from patriot_center_backend.cache.queries.transaction_queries import (
    get_trade_history_between_two_managers,
)
from patriot_center_backend.cache.updaters._validators import (
    validate_manager_query,
)
from patriot_center_backend.utils.image_url_handler import get_image_url


def get_head_to_head(
    manager1: str, manager2: str, year: str | None = None
) -> dict[str, Any]:
    """Get comprehensive head-to-head analysis between two managers.

    Iterates through all matchups to find:
    - Overall win/loss/tie record
    - Average margin of victory for each manager
    - Last win for each manager (most recent)
    - Biggest blowout for each manager

    Args:
        manager1: First manager name
        manager2: Second manager name
        year: Season year (optional - defaults to all-time)

    Returns:
        dictionary with all head-to-head data, including overall data,
            matchup history, and trades between the two managers
    """
    validate_manager_query(manager1, year)
    validate_manager_query(manager2, year)

    trades_between = get_trade_history_between_two_managers(
        manager1, manager2, year=year
    )

    return_dict = {
        "manager_1": get_image_url(manager1),
        "manager_2": get_image_url(manager2),
        "overall": get_head_to_head_overall_from_cache(
            manager1, manager2, year=year
        ),
        "matchup_history": get_head_to_head_overall_from_cache(
            manager1, manager2, year=year, list_all_matchups=True
        ),
        "trades_between": {
            "total": len(trades_between),
            "trade_history": trades_between,
        },
    }

    return deepcopy(return_dict)
