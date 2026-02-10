"""Queries for replacement score cache."""

from copy import deepcopy
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER


def get_replacement_scores(year: int, week: int) -> dict[str, Any]:
    """Get the replacement score for a given week.

    Args:
        year: The NFL season year (e.g., 2024).
        week: The week number (1-17).

    Returns:
        The replacement score for the given week.
    """
    replacement_score_cache = CACHE_MANAGER.get_replacement_score_cache()

    replacement_scores = (
        replacement_score_cache.get(str(year), {}).get(str(week), {})
    )

    return deepcopy(replacement_scores)
