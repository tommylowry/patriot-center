"""This module provides utility for interacting with the Sleeper API."""

import logging
from typing import Any

import requests

from patriot_center_backend.constants import (
    LEAGUE_IDS,
    USERNAME_TO_REAL_NAME,
)
from patriot_center_backend.utils.helpers import get_user_id

SLEEPER_API_URL = "https://api.sleeper.app/v1"

logger = logging.getLogger(__name__)


def fetch_sleeper_data(endpoint: str) -> dict[str, Any] | list[Any]:
    """Fetches data from the Sleeper API given an endpoint.

    Args:
        endpoint: The endpoint to call on the Sleeper API.

    Returns:
        The parsed JSON response from the Sleeper API.

    Raises:
        ConnectionAbortedError: If the request to the Sleeper API fails.
    """
    url = f"{SLEEPER_API_URL}/{endpoint}"

    response = requests.get(url)

    if response.status_code != 200:
        raise ConnectionAbortedError(
            f"Failed to fetch data from Sleeper API with call to {url}"
        )

    # Return parsed JSON
    return response.json()


def get_roster_id(
    user_id: str,
    year: int,
    sleeper_rosters_response: list[dict[str, Any]] | None = None,
) -> int | None:
    """Retrieves a roster ID for a given user ID and year.

    Args:
        user_id: The user ID to retrieve the roster ID for.
        year: The year to retrieve the roster ID for.
        sleeper_rosters_response: The response from the Sleeper API call
            to retrieve rosters for a given year. If not provided,
            it will be fetched.

    Returns:
        The roster ID for the given user ID and year,
            or None if the user ID is not found.

    Raises:
        ValueError: If the Sleeper API call fails to retrieve
            the rosters in list form.
    """
    if not sleeper_rosters_response:
        sleeper_response = fetch_sleeper_data(
            f"league/{LEAGUE_IDS[year]}/rosters"
        )

        # Make sure the rosters data is in list form
        if isinstance(sleeper_response, list):
            sleeper_rosters_response = sleeper_response
        else:
            raise ValueError(
                f"Sleeper API call failed to retrieve rosters in "
                f"list form for year {year}"
            )

    # Iterate over the rosters data and find the roster ID for the given user ID
    skipped_roster_id = None
    for user in sleeper_rosters_response:
        if user["owner_id"] == user_id:
            return user["roster_id"]

        # In 2024 special case, if there is only one user missing,
        #   assign them the roster_id missing from the roster_ids
        elif user["owner_id"] is None:
            skipped_roster_id = user["roster_id"]

    if year == 2024 and skipped_roster_id is not None:
        return skipped_roster_id

    logger.warning(f"User ID {user_id} not found in rosters for year {year}")
    return None


def get_roster_ids(year: int, week: int) -> dict[int, str]:
    """Retrieves a mapping of roster IDs to real names for a given year.

    Special Cases:
    - Davey: In 2024, if there is only one user missing,
        assign them the roster_id missing from the roster_ids
    - Tommy: In 2019 weeks 1-3, replace Cody's roster ID with Tommy

    Args:
        year: The year for which to retrieve the roster IDs.
        week: The week for which to retrieve the roster IDs.

    Returns:
        Mapping of roster IDs to real names.

    Raises:
        ValueError: If the Sleeper API call fails to retrieve
            the users in list form.
        Exception: If not all roster IDs are assigned to a user.
    """
    user_ids = {}

    sleeper_response = fetch_sleeper_data(f"league/{LEAGUE_IDS[year]}/users")

    # Make sure the users data is in list form
    if isinstance(sleeper_response, list):
        sleeper_users_response = sleeper_response
    else:
        raise ValueError(
            f"Sleeper API call failed to retrieve users in "
            f"list form for year {year}"
        )

    # Iterate over the users data and store the user IDs with their real names
    for user in sleeper_users_response:
        user_ids[user["user_id"]] = USERNAME_TO_REAL_NAME[user["display_name"]]

    roster_ids = {}

    # Fetch the rosters data from the Sleeper API
    sleeper_response = fetch_sleeper_data(f"league/{LEAGUE_IDS[year]}/rosters")

    # Make sure the rosters data is in list form
    if isinstance(sleeper_response, list):
        sleeper_rosters_response = sleeper_response
    else:
        raise ValueError(
            f"Sleeper API call failed to retrieve rosters in "
            f"list form for year {year}"
        )

    # Iterate over the rosters data and store the roster IDs
    for user in sleeper_rosters_response:
        user_id = user["owner_id"]
        roster_id = get_roster_id(
            user_id, year, sleeper_rosters_response=sleeper_rosters_response
        )

        if not isinstance(roster_id, int):
            continue

        # In 2024 special case, if user_id is None,
        #   assign the roster_id to "Davey"
        if year == 2024 and user_id is None:
            roster_ids[roster_id] = "Davey"
            continue

        # In 2019 special case, Tommy started the year
        #   and Cody took over in week 4
        if year == 2019 and week <= 3 and user_ids[user_id] == "Cody":
            roster_ids[roster_id] = "Tommy"
            continue

        # Store the roster ID and the real name of the user
        roster_ids[roster_id] = user_ids[user_id]

    if len(roster_ids) > len(user_ids):
        raise Exception("Not all roster IDs are assigned to a user")

    return roster_ids


def get_league_info(year: int) -> dict[str, Any]:
    """Retrieves the league metadata for a given year.

    Args:
        year: The year for which to retrieve the league metadata.

    Returns:
        The league metadata.

    Raises:
        ValueError: If no league ID is found for the given year.
    """
    league_id = LEAGUE_IDS.get(year)
    if not league_id:
        raise ValueError(f"No league ID found for year {year}.")

    # Query Sleeper API for league metadata
    league_info = fetch_sleeper_data(f"league/{league_id}")
    if not isinstance(league_info, dict):
        raise ValueError(
            f"Sleeper API call failed to retrieve "
            f"league info for year {year}"
        )

    return league_info


def fetch_user_metadata(manager_name: str) -> dict[str, Any]:
    """Retrieves the user metadata for a given manager name.

    Args:
        manager_name: The name of the manager.

    Returns:
        The user metadata.

    Raises:
        ValueError: If no user ID is found for the given manager name.
    """
    user_id = get_user_id(manager_name)
    if not user_id:
        raise ValueError(f"No user ID found for manager {manager_name}.")

    # Query Sleeper API for user metadata
    sleeper_response = fetch_sleeper_data(f"users/{user_id}")
    if not sleeper_response or not isinstance(sleeper_response, dict):
        raise ValueError(
            f"Sleeper API call failed to retrieve user info "
            f"for user ID {user_id}"
        )

    return sleeper_response
