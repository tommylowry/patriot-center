"""Progress tracker for weekly data updater."""

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.utils.sleeper_helpers import get_league_info


def get_league_status(year: int) -> tuple[list[int], bool]:
    """Get the weeks that need to be updated and whether the season is complete.

    Args:
        year: Year to check

    Returns:
        List of weeks that need to be updated
        Whether the season is complete
    """
    last_updated_year, last_updated_week = _get_last_updated()
    league_info = get_league_info(year)

    week = league_info["settings"]["last_scored_leg"]
    season_complete = league_info["status"] == "complete"

    # Year already finished
    if year < last_updated_year:
        return [], season_complete

    # New year
    if year > last_updated_year:
        return list(range(1, week + 1)), season_complete

    # Year is up to date, check weeks
    # Week already finished
    if week <= last_updated_week:
        return [], season_complete

    # New week
    return list(range(last_updated_week + 1, week + 1)), season_complete


def set_last_updated(year: int, week: int) -> None:
    """Set the last updated year and week.

    Args:
        year: Year to set
        week: Week to set
    """
    weekly_data_progress = CACHE_MANAGER.get_weekly_data_progress_tracker()
    weekly_data_progress["year"] = year
    weekly_data_progress["week"] = week


def _get_last_updated() -> tuple[int, int]:
    """Get the last updated year and week.

    Returns:
        Last updated year and week, or (0, 0) if not set
    """
    weekly_data_progress = CACHE_MANAGER.get_weekly_data_progress_tracker()

    if not weekly_data_progress:
        set_last_updated(0, 0)
        return 0, 0

    return weekly_data_progress["year"], weekly_data_progress["week"]
