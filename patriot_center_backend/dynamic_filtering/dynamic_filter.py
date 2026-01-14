"""Functions for finding valid filtering options based on selected criteria."""

from typing import Dict, List

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.dynamic_filtering.find_valid_options import (
    find_valid_managers,
    find_valid_positions,
    find_valid_weeks,
    find_valid_years,
)
from patriot_center_backend.dynamic_filtering.formatter import format_output
from patriot_center_backend.dynamic_filtering.validator import validate_dynamic_filter_args


def filter(
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        position: str | None = None,
        player: str | None = None,
    ) -> Dict[str, List[str]]:
    """Returns valid filter options given current selections.

    Args:
        year: The year of the data to filter.
        week: The week of the data to filter.
        manager: The manager of the data to filter.
        position: The position of the data to filter.
        player: The player of the data to filter.

    Returns:
        Dictionary with keys "years", "weeks", "managers", and "positions",
            each containing a list of valid string options.
    """
    
    validate_dynamic_filter_args(year, week, manager, position, player)

    players_cache = CACHE_MANAGER.get_players_cache()
    
    # Lock position if player selected
    positions = set()
    if player:
        position = players_cache[player]["position"]
        positions = set([position])
    
    # Each function returns (matching_items, should_include_all)
    years = find_valid_years(manager, position, player)
    weeks = find_valid_weeks(year, manager, position, player)
    managers = find_valid_managers(year, week, position, player)
    if not positions:
        positions = find_valid_positions(year, week, manager)
    
    return format_output(years, weeks, managers, positions)