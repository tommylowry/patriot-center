"""
Player data access layer for the Patriot Center backend.

This module provides simple getter functions for accessing cached player data
and valid filtering options. These functions wrap the cache loading utilities
and are used by services that need player metadata or validation information.
"""
from patriot_center_backend.utils.cache_utils import load_cache
from patriot_center_backend.constants import PLAYERS_CACHE_FILE, VALID_OPTIONS_CACHE_FILE

def fetch_players():
    """
    Retrieve the complete player metadata cache.

    Loads player information including names, positions, teams, and slugs.
    This cache is maintained by the starters_loader and updated incrementally.

    Returns:
        dict: Player cache with player names as keys, each containing:
            - full_name (str): Complete player name
            - first_name (str): Player's first name
            - last_name (str): Player's last name
            - position (str): Player's position (QB, RB, WR, TE, K, DEF)
            - team (str): NFL team abbreviation
            - slug (str): URL-friendly player identifier
    """
    return load_cache(PLAYERS_CACHE_FILE, initialize_with_last_updated_info=False)

def fetch_valid_options_cache():
    """
    Retrieve the valid filtering options cache.

    Provides metadata about what filters are available and valid for the UI.
    Includes information about which years, weeks, managers, players, and
    positions are present in the dataset.

    Returns:
        dict: Valid options cache structured by season and week, containing:
            - years (list): Available seasons
            - weeks (list): Available weeks per season
            - managers (list): Manager names with data
            - players (list): Players who have appeared
            - positions (list): Positions represented in the data
    """
    return load_cache(VALID_OPTIONS_CACHE_FILE)