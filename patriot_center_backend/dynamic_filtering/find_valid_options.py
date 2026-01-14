"""Functions for finding valid filtering options based on selected criteria."""

import logging
from typing import List, Set

from patriot_center_backend.cache import CACHE_MANAGER

logger = logging.getLogger(__name__)


def find_valid_years(manager: str | None, position: str | None,
                     player: str | None) -> Set[str]:
    """Finds years that have data matching the filters.

    Args:
        manager: The manager to filter by.
        position: The position to filter by.
        player: The player to filter by.

    Returns:
        A set of years that match the filters.
    """

    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    if not manager and not position and not player:
        return set(valid_options_cache.keys())

    valid = set()

    for yr, year_data in valid_options_cache.items():
        year_valid = False

        for wk in year_data.get("weeks", []):
            week_data = year_data.get(wk, {})

            if manager:
                if manager not in week_data.get("managers", []):
                    continue

                manager_data = week_data.get(manager, {})
                if position and position not in manager_data.get(
                        "positions", []):
                    continue
                if player and player not in manager_data.get("players", []):
                    continue

            else:
                if position and position not in week_data.get("positions", []):
                    continue
                if player and player not in week_data.get("players", []):
                    continue

            year_valid = True
            break

        if year_valid:
            valid.add(yr)

    if not valid:
        logger.warning("No valid years found.")

    return valid


def find_valid_weeks(year: str | None, manager: str | None,
                     position: str | None, player: str | None) -> Set[str]:
    """Find weeks that have data matching the filters.

    Args:
        year: The year to filter by.
        manager: The manager to filter by.
        position: The position to filter by.
        player: The player to filter by.

    Returns:
        A set of weeks that match the filters.
    """

    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    valid = set()
    years_to_check = [year] if year else valid_options_cache.keys()

    for yr in years_to_check:
        year_data = valid_options_cache.get(yr, {})
        for wk in year_data.get("weeks", []):
            week_data = year_data.get(wk, {})

            if manager:
                if manager not in week_data.get("managers", []):
                    continue

                manager_data = week_data.get(manager, {})
                if position and position not in manager_data.get(
                        "positions", []):
                    continue
                if player and player not in manager_data.get("players", []):
                    continue

            else:
                if position and position not in week_data.get("positions", []):
                    continue
                if player and player not in week_data.get("players", []):
                    continue

            valid.add(wk)

    if not valid:
        logger.warning("No valid weeks found.")

    return valid


def find_valid_managers(year: str | None, week: str | None,
                        position: str | None, player: str | None) -> Set[str]:
    """Finds managers that have data matching the filters.

    Args:
        year: The year to filter by.
        week: The week to filter by.
        position: The position to filter by.
        player: The player to filter by.

    Returns:
        A set of managers that match the filters.
    """

    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    valid = set()

    # Set years to check to year if set, otherwise all
    years_to_check = [year] if year else valid_options_cache.keys()

    weeks_to_check = _get_weeks_to_check(year, week)

    for yr in years_to_check:
        year_data = valid_options_cache.get(yr, {})

        if not weeks_to_check:
            weeks_to_check = year_data.get("weeks", [])

        for wk in weeks_to_check:
            week_data = year_data.get(wk, {})

            for mgr in week_data.get("managers", []):
                manager_data = week_data.get(mgr, {})

                if position and position not in manager_data.get(
                        "positions", []):
                    continue
                if player and player not in manager_data.get("players", []):
                    continue
                valid.add(mgr)

    if not valid:
        logger.warning("No valid managers found.")

    return valid


def find_valid_positions(year: str | None, week: str | None,
                         manager: str | None) -> Set[str]:
    """Finds positions that have data matching the filters.

    Args:
        year: The year to filter by.
        week: The week to filter by.
        manager: The manager to filter by.

    Returns:
        A set of positions that match the filters.
    """

    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    valid = set()

    # Set years to check to year if set, otherwise all
    years_to_check = [year] if year else valid_options_cache.keys()

    weeks_to_check = _get_weeks_to_check(year, week)

    for yr in years_to_check:
        year_data = valid_options_cache.get(yr, {})

        if not weeks_to_check:
            weeks_to_check = year_data.get("weeks", [])

        for wk in weeks_to_check:
            week_data = year_data.get(wk, {})

            if manager:
                if manager not in week_data.get("managers", []):
                    continue
                valid.update(week_data.get(manager, {}).get("positions", []))
            else:
                valid.update(week_data.get("positions", []))

    if not valid:
        logger.warning("No valid positions found.")

    return valid


def _get_weeks_to_check(year: str | None, week: str | None) -> List[str]:
    """Determines which weeks to iterate over.

    If `week` is provided, it is the only week to check.
    If `year` is provided, all weeks in that year are checked.
    If neither `year` nor `week` is provided, no weeks are checked.

    Args:
        year: The year to filter by.
        week: The week to filter by.

    Returns:
        A list of weeks to check.
    """

    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    if week:
        return [week]
    if year:
        return valid_options_cache.get(year, {}).get("weeks", [])
    return []  # Will be populated per-year in the loop
