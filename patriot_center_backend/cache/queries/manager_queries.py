"""Cache query helpers for manager metadata."""

import logging
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS

logger = logging.getLogger(__name__)


def get_manager_summary_from_cache(manager_name: str) -> dict[str, Any]:
    """Get manager summary from cache.

    Args:
        manager_name: The name of the manager.

    Returns:
        Dictionary of manager summary.

    Raises:
        ValueError: If the manager is not found in the cache.
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()
    return_summary = manager_cache.get(manager_name, {}).get("summary", {})

    if not return_summary:
        raise ValueError(f"Manager {manager_name} not found in cache.")

    return return_summary


def get_list_of_managers_from_cache(active_only: bool) -> list[str]:
    """Get a list of all managers in the cache.

    Args:
        active_only: If True, only return active managers.

    Returns:
        A list of manager names.
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    current_year = str(max(LEAGUE_IDS.keys()))

    if active_only:
        return valid_options_cache[current_year]["managers"]
    if not active_only:
        return list(manager_cache.keys())


def get_manager_years_active_from_cache(manager_name: str) -> list[str]:
    """Get a list of years a manager has been active.

    Args:
        manager_name: The name of the manager.

    Returns:
        A list of years the manager has been active.

    Raises:
        ValueError: If the manager is not found in the cache.
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    if "years" not in manager_cache[manager_name]:
        raise ValueError(f"Manager {manager_name} not found in cache.")
    return list(manager_cache[manager_name]["years"].keys())
