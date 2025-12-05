"""
Service helpers for querying starters cache.

Provides filtered views over the starters cache by:
- season and/or week
- manager (optionally constrained by season/week)

Notes:
- STARTERS_CACHE is loaded at import time to serve requests quickly.
- Returns empty dicts on missing seasons/weeks/managers instead of raising.
"""
from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

STARTERS_CACHE = load_or_update_starters_cache()

def fetch_starters(manager=None, season=None, week=None, lists_only=False):
    """
    Public entry point for retrieving starters slices.

    Dispatches to either season/week filtering or manager-centric filtering.

    Args:
        manager (str | None): Manager username (raw key in cache).
        season (int | None): Season identifier.
        week (int | None): Week number (1-17).

    Returns:
        dict: Nested dict shaped like STARTERS_CACHE subset.
    """
    if season is None and week is None and manager is None:
        # Full cache passthrough for unfiltered requests
        if lists_only:
            return _lists_only(STARTERS_CACHE)
        else:
            return _remove_lists(STARTERS_CACHE)

    if manager is None:
        filtered_dict = _filter_by_season_and_week(season, week)
        if lists_only:
            return _lists_only(filtered_dict)
        else:
            return _remove_lists(filtered_dict)
    
    filtered_dict = _filter_by_manager(manager, season, week)
    if lists_only:
        return _lists_only(filtered_dict)
    else:
        return _remove_lists(filtered_dict)

def _filter_by_season_and_week(season, week, lists_only=False):
    """
    Slice cache down to season and optionally week.

    Args:
        season (int): Season identifier (must exist in cache).
        week (int | None): Week number to narrow further.

    Returns:
        dict: {season: {...}} or {season: {week: {...}}} or {} if not found.
    """
    season_str = str(season)
    if season_str not in STARTERS_CACHE:
        return {}

    if week is not None:
        week_str = str(week)
        if week_str not in STARTERS_CACHE[season_str]:
            return {}
        return {
            season_str: {
                week_str: STARTERS_CACHE[season_str][week_str]
            }
        }

    return {season_str: STARTERS_CACHE[season_str]}

def _filter_by_manager(manager, season, week, lists_only=False):
    """
    Extract only data for one manager, optionally restricted by season/week.

    Iterates through cache (skipping metadata keys) and collects matches.

    Args:
        manager (str): Manager username.
        season (int | None): Season constraint.
        week (int | None): Week constraint.

    Returns:
        dict: Nested dict {season: {week: {manager: players}}}
    """
    filtered_data = {}

    for season_key, weeks in STARTERS_CACHE.items():
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
                filtered_data.setdefault(season_key, {}).setdefault(week_key, {})
                filtered_data[season_key][week_key][manager] = starters[manager]

    return filtered_data

def _lists_only(data_dict):
    """
    Remove all non-list entries from nested dict.
    """
    keys_to_keep = ["managers", "players", "positions", "weeks"]
    new_dict = {}
    year_dict = {}
    for year, yearly_items in data_dict.items():
        for week, weekly_items in yearly_items.items():
            if week in keys_to_keep:
                year_dict[week] = weekly_items
                continue

            manager_dict = {}
            for manager, manager_items in weekly_items.items():
                if manager in keys_to_keep:
                    manager_dict[manager] = manager_items
                    continue

                player_dict = {}
                for player, player_data in manager_items.items():
                    if player in keys_to_keep:
                        player_dict[player] = player_data
                    manager_dict[manager] = player_dict
            year_dict[week] = manager_dict
        new_dict[year] = year_dict
            
    return new_dict
            

def _remove_lists(data_dict):

    keys_to_remove = ["managers", "players", "positions", "weeks"]
    
    new_dict = {}
    for year, yearly_items in data_dict.items():
        
        if year in keys_to_remove:
            continue
        
        year_dict = {}
        for week, weekly_items in yearly_items.items():
            
            if week in keys_to_remove:
                continue
            
            week_dict = {}
            for manager, manager_items in weekly_items.items():
                
                if manager in keys_to_remove:
                    continue
                
                manager_dict = {}
                for player, player_data in manager_items.items():
                    if player in keys_to_remove:
                        continue
                    manager_dict[player] = player_data
                
                week_dict[manager] = manager_dict
            
            year_dict[week] = week_dict
        new_dict[year] = year_dict
            
    return new_dict

fetch = fetch_starters(lists_only=True)
print(fetch)