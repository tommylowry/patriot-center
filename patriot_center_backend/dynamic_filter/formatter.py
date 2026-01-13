"""Functions for formatting the output of the dynamic filter."""

from typing import Dict, List, Set


def format_output(
        years: Set[str],
        weeks: Set[str],
        managers: Set[str],
        positions: Set[str]
    ) -> Dict[str, List[str]]:
    """Formats the output of the dynamic filter into a dictionary.

    Args:
        years: Set of year strings
        weeks: Set of week strings
        managers: Set of manager strings
        positions: Set of position strings

    Returns:
        A dictionary with keys "years", "weeks", "managers", and "positions",
        each containing a sorted list of strings
    """

    result = {
        "years": sorted(years, reverse=True),
        "weeks": format_weeks(weeks),
        "managers": sorted(managers),
        "positions": format_positions(positions)
    }
    return result

def format_weeks(weeks: Set[str]) -> List[str]:
    """Formats a set of week numbers into a sorted list of strings.

    Args:
        weeks: Set of week numbers as strings

    Returns:
        A sorted list of week numbers as strings
    """

    weeks_list = list([int(week) for week in weeks])
    weeks_list = sorted(weeks_list)
    weeks_list = [str(week) for week in weeks_list]
    return weeks_list

def format_positions(positions: Set[str]) -> List[str]:
    """Formats a set of position strings into a sorted list of strings.

    The positions are sorted in the order of (QB, RB, WR, TE, K, DEF).

    Args:
        positions (Set[str]): Set of position strings

    Returns:
        List[str]: A sorted list of position strings
    """

    desired_order = ["QB", "RB", "WR", "TE", "K", "DEF"]
    positions_list = sorted(
        [p for p in positions if p in desired_order],
        key=lambda x: desired_order.index(x)
    )
    return positions_list
