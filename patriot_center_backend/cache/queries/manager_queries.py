"""Cache query helpers for manager metadata."""

import logging
from copy import deepcopy
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER

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
    manager_cache = CACHE_MANAGER.get_manager_metadata_cache()
    return_summary = deepcopy(
        manager_cache.get(manager_name, {}).get("summary", {})
    )

    if not return_summary:
        raise ValueError(f"Manager {manager_name} not found in cache.")

    return return_summary
