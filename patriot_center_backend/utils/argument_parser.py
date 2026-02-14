"""Utilities for parsing arguments into year, week, and manager."""

from patriot_center_backend.constants import LEAGUE_IDS, USER_IDS
from patriot_center_backend.models import Manager


def parse_arguments(
    arg1: str | None, arg2: str | None, arg3: str | None
) -> tuple[str | None, str | None, Manager | None]:
    """Parse provided arguments into year, week, and manager.

    Args:
        arg1 (str | None): Season (year) or week number or manager name.
        arg2 (str | None): Season (year) or week number or manager name.
        arg3 (str | None): Season (year) or week number or manager name.

    Returns:
        tuple[str | None, str | None, str | None]: Year, week, and manager.

    Raises:
        ValueError: If multiple arguments of the same type are provided
            or invalid.
    """
    # Initialize result values
    year = None
    manager = None
    week = None

    # Iterate through all provided arguments and classify each
    for arg in (arg1, arg2, arg3):
        if arg is None:
            continue

        arg_int = int(arg)
        # Check if it matches a known league year
        if arg_int in LEAGUE_IDS:
            if year is not None:
                raise ValueError("Multiple year arguments provided.")
            year = arg
            continue
        # Check if it's a valid week number (1-17)
        elif 1 <= arg_int <= 17:
            if week is not None:
                raise ValueError("Multiple week arguments provided.")
            week = arg
            continue
        elif arg in USER_IDS:
            if manager is not None:
                raise ValueError("Multiple manager arguments provided.")
            manager = Manager(arg)
            continue
        else:
            raise ValueError(f"Invalid argument provided: {arg}")

    # Validate that week is only provided with year (week alone is ambiguous)
    if week is not None and year is None:
        raise ValueError("Week provided without a corresponding year.")

    return year, week, manager
