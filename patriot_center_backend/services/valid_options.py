from typing import Dict, List, Set

from patriot_center_backend.cache import CACHE_MANAGER


def get_valid_options(
        year: str | None = None,
        week: str | None = None,
        manager: str | None = None,
        position: str | None = None,
        player: str | None = None,
    ) -> Dict[str, List[str]]:
    """Returns valid filter options given current selections."""

    players_cache = CACHE_MANAGER.get_players_cache()
    
    # Lock position if player selected
    positions = set()
    if player:
        position = players_cache[player]["position"]
        positions = set([position])
    
    # Each function returns (matching_items, should_include_all)
    years     = find_valid_years(manager, position, player)
    weeks     = find_valid_weeks(year, manager, position, player)
    managers  = find_valid_managers(year, week, position, player)
    if not positions:
        positions = find_valid_positions(year, week, manager)
    
    return format_output(years, weeks, managers, positions)


def find_valid_years(
        manager: str | None,
        position: str | None,
        player: str | None
    ) -> Set[str]:
    """Find years that have data matching the filters."""
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    valid = set()

    for yr, data in valid_options_cache.items():
        if manager and manager not in data.get("managers", []):
            continue
        if position and position not in data.get("positions", []):
            continue
        if player and player not in data.get("players", []):
            continue
        valid.add(yr)
    
    return valid


def find_valid_weeks(
        year: str | None,
        manager: str | None,
        position: str | None,
        player: str | None
    ) -> Set[str]:
    """Find weeks that have data matching the filters."""
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    valid = set()
    years_to_check = [year] if year else valid_options_cache.keys()
    
    for yr in years_to_check:
        year_data = valid_options_cache.get(yr, {})
        for wk in year_data.get("weeks", []):
            week_data = year_data.get(wk, {})
            if manager and manager not in week_data.get("managers", []):
                continue
            if position and position not in week_data.get("positions", []):
                continue
            if player and player not in week_data.get("players", []):
                continue
            valid.add(wk)
    return valid


def find_valid_managers(
        year: str | None,
        week: str | None,
        position: str | None,
        player: str | None
    ) -> Set[str]:
    """Find managers that have data matching the filters."""
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    valid = set()

    # Set years to check to year if set, otherwise all
    years_to_check = [year] if year else valid_options_cache.keys()
    
    # Set weeks to check to week if set
    if week:
        weeks_to_check = [year]
    # If year is set, check all weeks in that year
    elif year:
        weeks_to_check = valid_options_cache.get(year, {}).get("weeks", [])
    # If year is not set, check all weeks across all years
    else:
        weeks_to_check = []
    
    for yr in years_to_check:
        year_data = valid_options_cache.get(yr, {})
        
        if not weeks_to_check:
            weeks_to_check = year_data.get("weeks", [])
        
        for wk in weeks_to_check:
            week_data = year_data.get(wk, {})
            for mgr in week_data.get("managers", []):
                manager_data = week_data.get(mgr, {})
                if position and position not in manager_data.get("positions", []):
                    continue
                if player and player not in manager_data.get("players", []):
                    continue
                valid.add(mgr)
    return valid


def find_valid_positions(
        year: str | None,
        week: str | None,
        manager: str | None
    ) -> Set[str]:
    """Find positions that have data matching the filters."""
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    valid = set()

    # Set years to check to year if set, otherwise all
    years_to_check = [year] if year else valid_options_cache.keys()
    
    # Set weeks to check to week if set
    if week:
        weeks_to_check = [year]
    # If year is set, check all weeks in that year
    elif year:
        weeks_to_check = valid_options_cache.get(year, {}).get("weeks", [])
    # If year is not set, check all weeks across all years
    else:
        weeks_to_check = []
    
    for yr in years_to_check:
        year_data = valid_options_cache.get(yr, {})
        
        if not weeks_to_check:
            weeks_to_check = year_data.get("weeks", [])
        
        for wk in weeks_to_check:
            week_data = year_data.get(wk, {})

            managers_to_check = week_data.get("managers", [])
            if manager:
                if manager not in week_data.get("managers", []):
                    continue
                managers_to_check = [manager]
            
            for mgr in managers_to_check:
                manager_data = week_data.get(mgr, {})
                if 
            
            for mgr in week_data.get("managers", []):
                manager_data = week_data.get(mgr, {})
                
                if manager and manager not in manager_data.get("managers", []):
                    continue
                valid.add(mgr)
    return valid