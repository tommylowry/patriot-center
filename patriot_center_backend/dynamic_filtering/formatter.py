"""Functions for formatting the output of the dynamic filter."""


def format_output(
    years: set[str], weeks: set[str], managers: set[str], positions: set[str]
) -> dict[str, list[str]]:
    """Formats the output of the dynamic filter into a dictionary.

    Args:
        years: set of year strings
        weeks: set of week strings
        managers: set of manager strings
        positions: set of position strings

    Returns:
        A dictionary with keys "years", "weeks", "managers", and "positions",
        each containing a sorted list of strings
    """
    result = {
        "years": sorted(years, reverse=True),
        "weeks": format_weeks(weeks),
        "managers": sorted(managers),
        "positions": format_positions(positions),
    }
    return result


def format_weeks(weeks: set[str]) -> list[str]:
    """Formats a set of week numbers into a sorted list of strings.

    Args:
        weeks: set of week numbers as strings

    Returns:
        A sorted list of week numbers as strings
    """
    weeks_list = [int(week) for week in weeks]
    weeks_list = sorted(weeks_list)
    weeks_list = [str(week) for week in weeks_list]
    return weeks_list


def format_positions(positions: set[str]) -> list[str]:
    """Formats a set of position strings into a sorted list of strings.

    The positions are sorted in the order of (QB, RB, WR, TE, K, DEF).

    Args:
        positions: set of position strings

    Returns:
        A sorted list of position strings
    """
    desired_order = ["QB", "RB", "WR", "TE", "K", "DEF"]
    positions_list = sorted(
        [p for p in positions if p in desired_order],
        key=lambda x: desired_order.index(x),
    )
    return positions_list
