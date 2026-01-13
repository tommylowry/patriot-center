"""Validates dynamic filter arguments."""

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME


def validate_dynamic_filter_args(
        year: str | None,
        week: str | None,
        manager: str | None,
        position: str | None,
        player: str | None
    ) -> None:
    """Validates dynamic filter arguments.

    Args:
        year: The year of the data to filter.
        week: The week of the data to filter.
        manager: The manager of the data to filter.
        position: The position of the data to filter.
        player: The player of the data to filter.

    Raises:
        ValueError: If any of the filters are invalid.
    """

    if year and week and manager and position and player:
        raise ValueError("Cannot filter by year, week, manager, position, and player at the same time.")
    if week and not year:
        raise ValueError("Week filter cannot be applied without a Year filter.")
    
    validate_year(year)
    validate_week(week, year)
    validate_manager(manager, year, week)
    validate_position(position, year, week, manager)
    validate_player(player, year, week, manager, position)

def validate_year(year: str | None) -> None:
    """Validates the year argument.

    Args:
        year: The year of the data to filter.

    Raises:
        ValueError: If the year is invalid.
    """

    if not year:
        return
    if int(year) not in LEAGUE_IDS.keys():
        raise ValueError(f"Invalid year: {year}")

def validate_week(week: str | None, year: str | None) -> None:
    """Validates the week argument.

    Args:
        week: The week of the data to filter.
        year: The year of the data to filter.

    Raises:
        ValueError: If the week is invalid.
    """

    if not week:
        return

    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    if week not in valid_options_cache.get(year, {}).get("weeks", []):
        raise ValueError(f"Invalid week: {week}")

def validate_manager(
        manager: str | None,
        year: str | None,
        week: str | None
    ) -> None:
    """Validates the manager argument.

    Args:
        manager: The manager of the data to filter.
        year: The year of the data to filter.
        week: The week of the data to filter.

    Raises:
        ValueError: If the manager is invalid.
    """

    if not manager:
        return
    
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    if manager not in NAME_TO_MANAGER_USERNAME.keys():
        raise ValueError(f"Invalid manager: {manager}")
    
    if year and manager not in valid_options_cache.get(year, {}).get("managers", []):
        raise ValueError(f"Invalid manager: {manager}")

    if (year and week) and manager not in valid_options_cache.get(year, {}).get(week, {}).get("managers", []):
        raise ValueError(f"Invalid manager: {manager}")
    
def validate_position(
        position: str | None,
        year: str | None,
        week: str | None,
        manager: str | None
    ) -> None:
    """Validates the position argument.

    Args:
        position: The position of the data to filter.
        year: The year of the data to filter.
        week: The week of the data to filter.
        manager: The manager of the data to filter.

    Raises:
        ValueError: If the position is invalid.
    """

    if not position:
        return

    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    if position not in ["QB", "RB", "WR", "TE", "K", "DEF"]:
        raise ValueError(f"Invalid position: {position}")
    
    if year and position not in valid_options_cache.get(year, {}).get("positions", []):
        raise ValueError(f"Invalid position: {position}")
    
    if (year and week) and position not in valid_options_cache.get(year, {}).get(week, {}).get("positions", []):
        raise ValueError(f"Invalid position: {position}")
    
    if (year and manager) and position not in valid_options_cache.get(year, {}).get(manager, {}).get("positions", []):
        raise ValueError(f"Invalid position: {position}")
    
    if (year and week and manager) and position not in valid_options_cache.get(year, {}).get(week, {}).get(manager, {}).get("positions", []):
        raise ValueError(f"Invalid position: {position}")

def validate_player(
        player: str | None,
        year: str | None,
        week: str | None,
        manager: str | None,
        position: str | None
    ) -> None:
    """
    Validates the player argument.

    Args:
        player (str | None): The player of the data to filter.
        year (str | None): The year of the data to filter.
        week (str | None): The week of the data to filter.
        manager (str | None): The manager of the data to filter.
        position (str | None): The position of the data to filter.

    Raises:
        ValueError: If the player is invalid.
    """
    
    if not player:
        return
    
    players_cache = CACHE_MANAGER.get_players_cache()
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    if player not in players_cache.keys():
        raise ValueError(f"Invalid player: {player}")
    
    if position:
        if players_cache[player]["position"] != position:
            raise ValueError(f"Invalid player: {player}")
    
    if year and player not in valid_options_cache.get(year, {}).get("players", []):
        raise ValueError(f"Invalid player: {player}")
    
    if (year and week) and player not in valid_options_cache.get(year, {}).get(week, {}).get("players", []):
        raise ValueError(f"Invalid player: {player}")
    
    if (year and manager) and player not in valid_options_cache.get(year, {}).get(manager, {}).get("players", []):
        raise ValueError(f"Invalid player: {player}")
    
    if (year and week and manager) and player not in valid_options_cache.get(year, {}).get(week, {}).get(manager, {}).get("players", []):
        raise ValueError(f"Invalid player: {player}")
