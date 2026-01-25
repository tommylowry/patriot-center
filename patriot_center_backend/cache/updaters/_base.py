"""Base cache updater functions."""


def get_max_weeks(
    season: int,
    current_season: int | None = None,
    current_week: int | None = None,
    true_max: bool = False,
) -> int:
    """Determine maximum playable weeks for a season.

    Rules:
    - Live season -> current_week.
    - 2020 and earlier -> 16 (legacy rule set).
    - Other seasons -> 17 (regular season boundary).

    Args:
        season: The season to determine the max weeks for.
        current_season: The current season.
        current_week: The current week.
        true_max: If True, return the maximum possible weeks for the season, if
            False, return the cap at one week earlier.

    Returns:
        Max week to process for season.
    """
    if current_week is not None and season == current_season:
        return current_week  # Use the current week for the current season

    cap = 17 if season <= 2020 else 18
    return cap if true_max else cap - 1
