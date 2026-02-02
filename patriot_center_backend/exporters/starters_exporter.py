"""Starters exporter for starters data."""

from typing import Any

from patriot_center_backend.cache.queries.starters_queries import (
    get_starters_from_cache,
)


def get_starters(
    manager: str | None = None,
    season: int | None = None,
    week: int | None = None,
) -> dict[str, dict[str, dict[str, dict[str, Any]]]]:
    """Public entry point for retrieving starters slices.

    Dispatches to either season/week filtering or manager-centric filtering.

    Args:
        manager: Manager username (raw key in cache).
        season: Season identifier.
        week: Week number (1-17).

    Returns:
        Nested dict shaped like starters_cache subset.
    """
    return get_starters_from_cache(manager, season, week)
