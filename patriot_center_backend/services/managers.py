"""Service helpers for querying starters cache.

Provides filtered views over the starters cache by:
- season and/or week
- manager (optionally constrained by season/week)

Notes:
- Returns empty dicts on missing seasons/weeks/managers instead of raising.
"""

from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER


def fetch_starters(
    manager: str | None = None,
    season: int | None = None,
    week: int | None = None
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
    starters_cache = CACHE_MANAGER.get_starters_cache()

    if manager is None and season is not None:
        return _filter_by_season_and_week(season, week)

    if manager is not None:
        return _filter_by_manager(manager, season, week)

    # Full cache passthrough for unfiltered requests
    return starters_cache

def _filter_by_season_and_week(
    season: int, week: int | None = None
) -> dict[str, dict[str, dict[str, dict[str, Any]]]]:
    """Slice cache down to season and optionally week.

    Args:
        season: Season identifier (must exist in cache).
        week: Week number to narrow further.

    Returns:
        dict: Nested dict shaped like starters_cache subset.
    """
    starters_cache = CACHE_MANAGER.get_starters_cache()

    season_str = str(season)
    if season_str not in starters_cache:
        return {}

    if week is not None:
        week_str = str(week)
        if week_str not in starters_cache[season_str]:
            return {}
        return {
            season_str: {
                week_str: starters_cache[season_str][week_str]
            }
        }

    return {season_str: starters_cache[season_str]}

def _filter_by_manager(
    manager: str, season: int | None = None, week: int | None = None
) -> dict[str, dict[str, dict[str, dict[str, Any]]]]:
    """Extract only data for one manager, optionally restricted by season/week.

    Iterates through cache (skipping metadata keys) and collects matches.

    Args:
        manager: Manager name.
        season: Season constraint.
        week: Week constraint.

    Returns:
        Nested dict shaped like starters_cache subset.
    """
    starters_cache = CACHE_MANAGER.get_starters_cache()

    filtered_data = {}

    for season_key, weeks in starters_cache.items():
        # Skip metadata sentinel fields
        if season_key in ["Last_Updated_Season", "Last_Updated_Week"]:
            continue
        if season is not None and str(season) != season_key:
            continue

        for week_key, starters in weeks.items():
            if week is not None and str(week) != week_key:
                continue
            if manager in starters:
                # Initialize nested containers only when needed
                filtered_data.setdefault(
                    season_key, {}
                ).setdefault(
                    week_key, {}
                )
                filtered_data[season_key][week_key][manager] = starters[manager]

    return filtered_data
