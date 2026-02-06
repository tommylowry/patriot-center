"""Dynamic filter exporter for manager metadata."""

from patriot_center_backend.domains import Player
from patriot_center_backend.dynamic_filtering.dynamic_filter import (
    get_dynamic_filter_options_from_cache,
)


def get_dynamic_filter_options(
    year: str | None,
    week: str | None,
    manager: str | None,
    position: str | None,
    player: Player | None,
) -> dict[str, list[str]]:
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
    return get_dynamic_filter_options_from_cache(
        year, week, manager, position, player
    )
