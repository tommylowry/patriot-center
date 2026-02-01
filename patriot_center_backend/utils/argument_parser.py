"""Utilities for parsing arguments into year, week, and manager."""

from patriot_center_backend.constants import (
    LEAGUE_IDS,
    NAME_TO_MANAGER_USERNAME,
)


def parse_arguments(
    arg1: str | None, arg2: str | None, arg3: str | None
) -> tuple[int | None, int | None, str | None]:
    """Parse provided arguments into year, week, and manager.

    Args:
        arg1 (str | None): Season (year) or week number or manager name.
        arg2 (str | None): Season (year) or week number or manager name.
        arg3 (str | None): Season (year) or week number or manager name.

    Returns:
        tuple[int | None, int | None, str | None]: Year, week, and manager.

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

        # Numeric arguments: check if it's a year or week
        if arg.isnumeric():
            arg_int = int(arg)
            # Check if it matches a known league year
            if arg_int in LEAGUE_IDS:
                if year is not None:
                    raise ValueError("Multiple year arguments provided.")
                year = arg_int
            # Check if it's a valid week number (1-17)
            elif 1 <= arg_int <= 17:
                if week is not None:
                    raise ValueError("Multiple week arguments provided.")
                week = arg_int
            else:
                raise ValueError("Invalid integer argument provided.")
        else:
            # Non-numeric arguments: check if it's a manager name
            if arg in NAME_TO_MANAGER_USERNAME:
                if manager is not None:
                    raise ValueError("Multiple manager arguments provided.")
                manager = arg
                continue
            else:
                raise ValueError(f"Invalid argument provided: {arg}")

    # Validate that week is only provided with year (week alone is ambiguous)
    if week is not None and year is None:
        raise ValueError("Week provided without a corresponding year.")

    return year, week, manager
