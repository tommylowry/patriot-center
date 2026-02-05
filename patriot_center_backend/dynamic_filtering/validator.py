"""Validates dynamic filter arguments."""

from typing import Literal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import (
    LEAGUE_IDS,
    NAME_TO_MANAGER_USERNAME,
    Position,
)
from patriot_center_backend.domains.player import Player


def validate_dynamic_filter_args(
    year: str | None,
    week: str | None,
    manager: str | None,
    position: str | None,
    player: Player | None,
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
        raise ValueError(
            "Cannot filter by year, week, manager, position, and player "
            "at the same time."
        )

    _validate_year(year)
    _validate_week(week, year)
    _validate_manager(manager, year, week)
    _validate_position(position, year, week, manager)
    _validate_player(player, year, week, manager, position)


def _validate_year(year: str | None) -> None:
    """Validates the year argument.

    Args:
        year: The year of the data to filter.

    Raises:
        ValueError: If the year is invalid.
    """
    if not year:
        return
    if int(year) not in LEAGUE_IDS:
        raise ValueError(f"Invalid year: {year}")


def _validate_week(week: str | None, year: str | None) -> None:
    """Validates the week argument.

    Args:
        week: The week of the data to filter.
        year: The year of the data to filter.

    Raises:
        ValueError: If the week is invalid or cannot be applied.
    """
    if not week:
        return

    if not year:
        raise ValueError("Week filter cannot be applied without a Year filter.")

    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    if week not in valid_options_cache.get(year, {}).get("weeks", []):
        raise ValueError(f"Invalid week: {week}")


def _validate_manager(
    manager: str | None, year: str | None, week: str | None
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

    if manager not in NAME_TO_MANAGER_USERNAME:
        raise ValueError(f"Invalid manager: {manager}")

    if year:
        year_options = valid_options_cache.get(year, {})
        if manager not in year_options.get("managers", []):
            raise ValueError(f"Invalid manager: {manager}")
        if week:
            week_options = year_options.get(week, {})
            if manager not in week_options.get("managers", []):
                raise ValueError(f"Invalid manager: {manager}")


def _validate_position(
    position: str | None,
    year: str | None,
    week: str | None,
    manager: str | None,
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

    if position not in Position:
        raise ValueError(f"Invalid position: {position}")

    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    if year:
        year_options = valid_options_cache.get(year, {})
        if position not in year_options.get("positions", []):
            raise ValueError(f"Invalid position: {position}")

        if week:
            week_options = year_options.get(week, {})
            if position not in week_options.get("positions", []):
                raise ValueError(f"Invalid position: {position}")

            if manager:
                manager_options = week_options.get(manager, {})
                if position not in manager_options.get("positions", []):
                    raise ValueError(f"Invalid position: {position}")
                return

    if manager:
        _traverse_for_year_and_manager(year, manager, position, "position")


def _validate_player(
    player: Player | None,
    year: str | None,
    week: str | None,
    manager: str | None,
    position: str | None,
) -> None:
    """Validates the player argument.

    Args:
        player: The player of the data to filter.
        year: The year of the data to filter.
        week: The week of the data to filter.
        manager: The manager of the data to filter.
        position: The position of the data to filter.

    Raises:
        ValueError: If the player is invalid.
    """
    if not player:
        return

    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    error_str = f"Invalid player: {player.full_name} ({player})"

    if position and player.position != position:
        raise ValueError(error_str)

    if year:
        year_options = valid_options_cache.get(year, {})
        if str(player) not in year_options.get("players", []):
            raise ValueError(error_str)

        if week:
            week_options = year_options.get(week, {})
            if str(player) not in week_options.get("players", []):
                raise ValueError(error_str)

            if manager:
                manager_options = week_options.get(manager, {})
                if str(player) not in manager_options.get("players", []):
                    raise ValueError(error_str)
                return

    if manager:
        _traverse_for_year_and_manager(year, manager, player, "player")


def _traverse_for_year_and_manager(
    year: str | None,
    manager: str,
    item: Player | str,
    item_type: Literal["player", "position"],
) -> None:
    """Validates the item when filtering by year, manager, and player/position.

    Args:
        year: The year of the data to filter, if applicable.
        manager: The manager of the data to filter.
        item: The item of the data to filter.
            Must be either a player or a position.
        item_type: Either "player" or "position".

    Raises:
        ValueError: If the item is invalid.
    """
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    years_to_traverse = valid_options_cache.keys()
    if year:
        years_to_traverse = [year]

    for yr in years_to_traverse:
        yr_data = valid_options_cache.get(yr, {})

        # Check if item exists in ANY week for this manager
        for wk in yr_data.get("weeks", []):
            wk_data = yr_data.get(wk, {})
            if str(item) in wk_data.get(manager, {}).get(f"{item_type}s", []):
                return

    # Not found in any year
    if isinstance(item, Player):
        raise ValueError(f"Invalid player: {item.full_name} ({item})")
    raise ValueError(f"Invalid {item_type}: {item}")
