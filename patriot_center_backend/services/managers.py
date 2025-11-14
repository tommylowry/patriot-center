from patriot_center_backend.utils.player_ids_loader import load_player_ids
from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

PLAYER_IDS = load_player_ids()
STARTERS_CACHE = load_or_update_starters_cache()


def fetch_starters(manager=None, season=None, week=None):
    """
    Fetch starters data based on the provided parameters.

    Args:
        manager (str, optional): The manager to filter by.
        season (int, optional): The season to filter by.
        week (int, optional): The week to filter by.

    Returns:
        dict: The filtered starters data.
    """
    # If no parameters are provided, return the entire cache
    if season is None and week is None and manager is None:
        return STARTERS_CACHE

    # Filter by season and/or week
    if manager is None:
        return _filter_by_season_and_week(season, week)

    # Filter by manager
    return _filter_by_manager(manager, season, week)


def _filter_by_season_and_week(season, week):
    """
    Filter the starters cache by season and/or week.

    Args:
        season (int): The season to filter by.
        week (int, optional): The week to filter by.

    Returns:
        dict: The filtered starters data.
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


def _filter_by_manager(manager, season, week):
    """
    Filter the starters cache by manager, and optionally by season and/or week.

    Args:
        manager (str): The manager to filter by.
        season (int, optional): The season to filter by.
        week (int, optional): The week to filter by.

    Returns:
        dict: The filtered starters data.
    """
    filtered_data = {}

    for season_key, weeks in STARTERS_CACHE.items():
        # Skip metadata fields
        if season_key in ["Last_Updated_Season", "Last_Updated_Week"]:
            continue

        # If a specific season is provided, skip other seasons
        if season is not None and str(season) != season_key:
            continue

        for week_key, starters in weeks.items():
            # If a specific week is provided, skip other weeks
            if week is not None and str(week) != week_key:
                continue

            # If the manager exists in the starters, add it to the filtered data
            if manager in starters:
                if season_key not in filtered_data:
                    filtered_data[season_key] = {}
                if week_key not in filtered_data[season_key]:
                    filtered_data[season_key][week_key] = {}
                filtered_data[season_key][week_key][manager] = starters[manager]

    return filtered_data