"""This module provides utility for interacting with the Sleeper API."""

import logging
from math import ceil
from typing import Any, Literal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.calculations.player_score_calculator import (
    calculate_player_score,
)
from patriot_center_backend.constants import (
    LEAGUE_IDS,
    USERNAME_TO_REAL_NAME,
    Position,
)
from patriot_center_backend.domains import Player
from patriot_center_backend.utils.helpers import get_user_id
from patriot_center_backend.utils.sleeper_api import SLEEPER_CLIENT

logger = logging.getLogger(__name__)


def fetch_sleeper_data(
    endpoint: str, bypass_cache: bool = False
) -> dict[str, Any] | list[Any]:
    """Fetch data from the Sleeper API.

    Args:
        endpoint: The endpoint to call on the Sleeper API.
        bypass_cache: Whether to bypass the cache.

    Returns:
        The parsed JSON response from the Sleeper API.
    """
    return SLEEPER_CLIENT.fetch(endpoint, bypass_cache=bypass_cache)


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


def get_roster_ids(
    year: int, week: int, ignore_playoffs: bool = False
) -> dict[int, str]:
    """Retrieves a mapping of roster IDs to real names for a given year.

    Special Cases:
    - Davey: In 2024, if there is only one user missing,
        assign them the roster_id missing from the roster_ids
    - Tommy: In 2019 weeks 1-3, replace Cody's roster ID with Tommy

    Args:
        year: The year for which to retrieve the roster IDs.
        week: The week for which to retrieve the roster IDs.
        ignore_playoffs: Whether to return roster IDs for the playoffs only or
            for all weeks. Defaults to False, which returns roster IDs for the
            playoffs only if playoffs have started.

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

    if (
        get_season_state(str(year), str(week)) == "playoffs"
        and not ignore_playoffs
    ):
        playoff_ids = get_playoff_roster_ids(year, week)
        returning_ids = {}
        for id in playoff_ids:
            returning_ids[id] = roster_ids[id]

        return returning_ids

    return roster_ids


def get_playoff_roster_ids(year: int, week: int) -> list[int]:
    """Determine which rosters are participating in playoffs for a given week.

    Filters out regular year weeks and consolation bracket teams,
    returning only the roster IDs competing in the winners bracket.

    Rules:
    - 2019/2020: Playoffs start week 14 (rounds 1-3 for weeks 14-16).
    - 2021+: Playoffs start week 15 (rounds 1-3 for weeks 15-17).
    - Week 17 in 2019/2020 (round 4) is unsupported and raises an error.
    - Consolation bracket matchups (p=5) are excluded.

    Args:
        year (int): Target year year.
        week (int): Target week number.

    Returns:
        [int] or [] if regular year week.
              Empty dict signals no playoff filtering needed.

    Raises:
        ValueError: If week 17 in 2019/2020 or no rosters found for the round.
    """
    league_info = get_league_info(year)
    settings = league_info["settings"]
    playoff_type = settings["playoff_type"]
    playoff_week_start = settings["playoff_week_start"]
    num_playoff_teams = settings["playoff_teams"]

    if week < playoff_week_start:
        return []

    rounds_needed = ceil(num_playoff_teams / 2)

    # One week per round
    if playoff_type == 0:
        if week == playoff_week_start:
            round = 1
        elif week == playoff_week_start + 1:
            round = 2
        elif week == playoff_week_start + 2:
            round = 3
        else:
            return []
    # Two weeks Championship
    elif playoff_type == 1:
        if week == playoff_week_start:
            round = 1
        elif week == playoff_week_start + 1:
            round = 2
        elif week == playoff_week_start + 2 or week == playoff_week_start + 3:
            round = 3
        else:
            return []
    # Each round 2 weeks
    elif playoff_type == 2:
        if week == playoff_week_start or week == playoff_week_start + 1:
            round = 1
        elif week == playoff_week_start + 2 or week == playoff_week_start + 3:
            round = 2
        elif week == playoff_week_start + 4 or week == playoff_week_start + 5:
            round = 3
        else:
            return []
    else:
        logger.warning(
            f"Playoff type {playoff_type} not supported. "
            f"Returning empty playoff roster IDs.")
        return []

    if round > rounds_needed:
        return []



    sleeper_response_playoff_bracket = fetch_sleeper_data(
        f"league/{LEAGUE_IDS[year]}/winners_bracket"
    )

    if not isinstance(sleeper_response_playoff_bracket, list):
        raise ValueError("Cannot get playoff roster IDs for the given week")

    relevant_roster_ids = []
    for matchup in sleeper_response_playoff_bracket:
        if matchup.get("r") == round:
            if matchup.get("p") == 5:
                continue  # Skip consolation match
            relevant_roster_ids.append(matchup["t1"])
            relevant_roster_ids.append(matchup["t2"])

    if len(relevant_roster_ids) == 0:
        raise ValueError("Cannot get playoff roster IDs for the given week")

    return relevant_roster_ids


def get_season_state(
    year: str, week: str, playoff_week_start: int | None = None
) -> Literal["regular_season", "playoffs"]:
    """Determine the current state of the season (regular season or playoffs).

    Args:
        week: Current week number as string
        year: Current year as string
        playoff_week_start: Week when playoffs start
            (fetched from API if not provided)

    Returns:
        "regular_season" or "playoffs"

    Raises:
        ValueError: If week or year not provided
            or if Sleeper API call fails to retrieve what is expected
    """
    if not week or not year:
        raise ValueError("Week or Year not set. Cannot determine season state.")

    # Fetch playoff week start from league settings if not provided
    if not playoff_week_start:
        league_info = fetch_sleeper_data(f"league/{LEAGUE_IDS.get(int(year))}")

        if not isinstance(league_info, dict):
            raise ValueError(
                f"Sleeper API call failed to retrieve "
                f"league info for year {year}"
            )

        playoff_week_start = league_info.get("settings", {}).get(
            "playoff_week_start"
        )

        if not playoff_week_start:
            raise ValueError(
                f"Sleeper API call failed to retrieve "
                f"playoff_week_start for year {year}"
            )

    if int(week) >= playoff_week_start:
        return "playoffs"
    return "regular_season"


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
            f"Sleeper API call failed to retrieve league info for year {year}"
        )

    return league_info


def fetch_user_metadata(
    manager_name: str, bypass_cache: bool = False
) -> dict[str, Any]:
    """Retrieves the user metadata for a given manager name.

    Args:
        manager_name: The name of the manager.
        bypass_cache: Whether to bypass the cache.

    Returns:
        The user metadata.

    Raises:
        ValueError: If no user ID is found for the given manager name.
    """
    user_id = get_user_id(manager_name)
    if not user_id:
        raise ValueError(f"No user ID found for manager {manager_name}.")

    # Query Sleeper API for user metadata
    sleeper_response = fetch_sleeper_data(
        f"user/{user_id}", bypass_cache=bypass_cache
    )
    if not sleeper_response or not isinstance(sleeper_response, dict):
        raise ValueError(
            f"Sleeper API call failed to retrieve user info "
            f"for user ID {user_id}"
        )

    return sleeper_response


def fetch_all_player_ids() -> dict[str, Any]:
    """Retrieves the player metadata for a given manager name.

    Returns:
        The player metadata.

    Raises:
        ValueError: If Sleeper API call returns invalid data.
    """
    sleeper_response = fetch_sleeper_data("players/nfl")
    if not sleeper_response or not isinstance(sleeper_response, dict):
        raise ValueError("Sleeper API call failed to retrieve player info")

    return sleeper_response


def fetch_players(year: int, week: int) -> list[Player]:
    """Retrieves the player data for a given year and week.

    This function retrieves raw stats from the Sleeper API for the specified
    year and week, then calculates each player's fantasy score, their manager,
    and if they are a starter based on the league's scoring settings.

    Args:
        year: The year for which to retrieve player metadata.
        week: The week for which to retrieve player metadata.

    Returns:
        A list of Player objects.

    Raises:
        ValueError: If Sleeper API call returns invalid data.
    """
    week_data = fetch_sleeper_data(f"stats/nfl/regular/{year}/{week}")
    if not isinstance(week_data, dict):
        raise ValueError(
            f"Sleeper API call failed for year {year}, week {week}"
        )

    settings = fetch_sleeper_data(f"league/{LEAGUE_IDS[year]}")
    if not isinstance(settings, dict):
        raise ValueError(
            f"Sleeper API call failed to retrieve "
            f"scoring settings for year {year}"
        )
    scoring_settings = settings["scoring_settings"]

    players = []

    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()
    for player_id in week_data:
        if "TEAM_" in player_id:
            continue

        if player_ids_cache.get(player_id, {}).get("position") not in Position:
            continue

        player = Player(player_id)
        points = calculate_player_score(week_data[player_id], scoring_settings)
        player.set_week_data(str(year), str(week), points=points)

        players.append(player)

    matchup_data_response = fetch_sleeper_data(
        f"league/{LEAGUE_IDS[year]}/matchups/{week}"
    )
    if not isinstance(matchup_data_response, list):
        raise Exception(
            f"Could not fetch matchup data for season {year} week {week}"
        )
    roster_ids = get_roster_ids(year, week)

    for matchup in matchup_data_response:
        # Playoffs, skip that manager as the player
        # didn't start in a matchup that matters.
        if matchup["roster_id"] not in roster_ids:
            continue

        manager = roster_ids[matchup["roster_id"]]
        for player_id in matchup["players"]:
            player = Player(player_id)

            started = player_id in matchup["starters"]

            player.set_week_data(
                str(year), str(week), manager=manager, started=started
            )

    return players
