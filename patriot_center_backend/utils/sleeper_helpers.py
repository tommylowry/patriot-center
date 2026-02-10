"""This module provides utility for interacting with the Sleeper API."""

import logging
from copy import deepcopy
from math import ceil
from typing import Any, Literal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.calculations.player_score_calculator import (
    calculate_player_score,
)
from patriot_center_backend.constants import (
    LEAGUE_IDS,
    TOMMY_USER_ID,
    USERNAME_TO_REAL_NAME,
    Position,
)
from patriot_center_backend.models import Manager, Player
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
        response = fetch_sleeper_data(f"league/{LEAGUE_IDS[year]}/rosters")

        # Make sure the rosters data is in list form
        if not isinstance(response, list):
            raise ValueError(
                f"Sleeper API call failed to retrieve rosters in "
                f"list form for year {year}"
            )
        else:
            sleeper_rosters_response = response

    # Iterate over the rosters data and find the roster ID for the given user ID
    skipped_roster_id = None
    for user in sleeper_rosters_response:
        # If the user is a co-owner, skip them
        if user["co_owners"] and user_id in user["co_owners"]:
            return

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

    sleeper_users_response = fetch_sleeper_data(
        f"league/{LEAGUE_IDS[year]}/users"
    )

    # Make sure the users data is in list form
    if not isinstance(sleeper_users_response, list):
        raise ValueError(
            f"Sleeper API call failed to retrieve users in "
            f"list form for year {year}"
        )

    # Iterate over the users data and store the user IDs with their real names
    for user in sleeper_users_response:
        user_ids[user["user_id"]] = USERNAME_TO_REAL_NAME[user["display_name"]]

    roster_ids = {}

    # Fetch the rosters data from the Sleeper API
    sleeper_rosters_response = fetch_sleeper_data(
        f"league/{LEAGUE_IDS[year]}/rosters"
    )

    # Make sure the rosters data is in list form
    if not isinstance(sleeper_rosters_response, list):
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
            f"Returning empty playoff roster IDs."
        )
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


def get_playoff_weeks(year: int) -> list[int]:
    """Retrieves the week when playoffs start for a given year.

    Args:
        year: The year for which to retrieve the playoff week start.

    Returns:
        The playoff week start or None if no playoff week start is found.
    """
    league_info = get_league_info(year)
    start = league_info["settings"]["playoff_week_start"]
    end = league_info["settings"]["last_scored_leg"]

    return list(range(start, end + 1))


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


def fetch_matchups(year: int, week: int) -> list[dict[str, Any]]:
    """Retrieves the matchup data for a given year and week.

    Args:
        year: The year for which to retrieve matchup data.
        week: The week for which to retrieve matchup data.

    Returns:
        A list of matchup data dictionaries.
    """
    matchups = fetch_sleeper_data(f"league/{LEAGUE_IDS[year]}/matchups/{week}")
    if not isinstance(matchups, list):
        raise ValueError(
            f"Sleeper API call failed to retrieve matchup data "
            f"for year {year}, week {week}"
        )
    return matchups


def fetch_user_metadata(
    user_identifier: str, bypass_cache: bool = False
) -> dict[str, Any]:
    """Retrieves the user metadata for a given user identifier.

    Args:
        user_identifier: User identifier (user ID or username).
        bypass_cache: Whether to bypass the cache.

    Returns:
        The user metadata.

    Raises:
        ValueError: If no user ID is found for the given user identifier.
    """
    # Query Sleeper API for user metadata
    sleeper_response = fetch_sleeper_data(
        f"user/{user_identifier}", bypass_cache=bypass_cache
    )
    if not sleeper_response or not isinstance(sleeper_response, dict):
        raise ValueError(
            f"Sleeper API call failed to retrieve user info "
            f"for user {user_identifier}"
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

    return players


def set_managers_season_data(year: int, week: int) -> list[Manager]:
    """Sets the season data for all managers for a given year and week.

    This function retreives manager metadata from the Sleeper API for the
    specified year and week, then sets the season data for each manager.

    Args:
        year: The year for which to set the season data.
        week: The week for which to set the season data.

    Raises:
        ValueError: If the Sleeper API call fails to retrieve the managers.
    """
    managers = fetch_sleeper_data(f"league/{LEAGUE_IDS[year]}/users")
    if not isinstance(managers, list):
        raise ValueError(
            f"Sleeper API call failed to retrieve managers for year {year}"
        )

    league_info = get_league_info(year)
    season_complete = league_info["status"] == "complete"

    roster_ids = get_roster_ids(year, week)

    orphaned_manager_data = {}
    roster_ids_that_have_been_set = []

    returning_managers = []

    for manager_data in managers:
        roster_id = get_roster_id(manager_data["user_id"], year)

        # Handle Davey's case where he's not in the rosters in 2024
        if roster_id is None:
            orphaned_manager_data = deepcopy(manager_data)
            continue
        roster_ids_that_have_been_set.append(roster_id)

        manager = Manager(manager_data["user_id"])

        team_image_url = manager_data.get("metadata", {}).get("avatar")
        # For older leagues, team_image didn't exist
        if not team_image_url:
            team_image_url = manager.image_url

        team_name = manager_data.get("metadata", {}).get("team_name")
        # team_name is an optional field, so if it doesn't exist, use username
        if not team_name:
            team_name = manager.username

        # Handle Tommy's case where he's not in the users in 2019 for weeks 1-3
        if manager.real_name == "Cody" and year == 2019 and week <= 3:
            manager = Manager(TOMMY_USER_ID)
            team_image_url = manager.image_url
            team_name = "Tommy's 2019 Weeks 1-3 Team"

        manager.set_season_data(
            str(year), team_image_url, team_name, season_complete, roster_id
        )

        returning_managers.append(manager)

    # Set the roster ID for anyone who wasn't in the rosters (Davey's case)
    if orphaned_manager_data:
        for id in roster_ids:
            if id not in roster_ids_that_have_been_set:
                manager = Manager(orphaned_manager_data["user_id"])

                team_image_url = orphaned_manager_data["metadata"]["avatar"]
                team_name = orphaned_manager_data["metadata"]["team_name"]

                manager.set_season_data(
                    str(year),
                    team_image_url,
                    team_name,
                    season_complete,
                    id,  # Roster ID
                )
                returning_managers.append(manager)

    return returning_managers


def set_matchup_data(year: int, week: int, managers: list[Manager]) -> None:
    """Sets the week data for all managers for a given year and week.

    This function retreives manager metadata from the Sleeper API for the
    specified year and week, then sets the week data for each manager.

    Args:
        year: The year for which to set the week data.
        week: The week for which to set the week data.
        managers: A list of managers to set the week data for.

    Raises:
        ValueError: If the Sleeper API call fails to retrieve the managers.
    """
    matchups = fetch_matchups(year, week)
    roster_ids = get_roster_ids(year, week)

    # Create a mapping of matchup IDs to matchup data
    matchup_mapping: dict[int, dict[str, Any]] = {}
    roster_id_to_manager: dict[int, Manager] = {}

    # Create a mapping of roster IDs to managers
    for roster_id in list(roster_ids.keys()):
        for manager in managers:
            if manager.get_roster_id(str(year)) == roster_id:
                roster_id_to_manager[roster_id] = manager
                break

    # Loop through all matchups
    for manager_a_data in matchups:
        # Matchups that don't matter (consoluation bracket, etc.) are skipped
        if manager_a_data["roster_id"] not in roster_id_to_manager:
            continue

        # Set the Player data for each player that played and was rostered
        manager = roster_id_to_manager[manager_a_data["roster_id"]]
        starters = []
        rostered_players = []
        for player_id in manager_a_data["players"]:
            player = Player(player_id)
            rostered_players.append(player)

            started = player_id in manager_a_data["starters"]
            if started:
                starters.append(player)

            player.set_week_data(
                str(year), str(week), manager=manager, started=started
            )

        # Change the matchup data to include the Player objects
        manager_a_data["starters_objects"] = starters
        manager_a_data["players_objects"] = rostered_players

        # If we don't yet have matchup data for the other
        # manager wait until we do
        if manager_a_data["matchup_id"] not in matchup_mapping:
            matchup_mapping[manager_a_data["matchup_id"]] = manager_a_data
            continue

        # This manager's matchup data and their opponent's matchup data can now
        # be compared with the same matchup ID
        manager_b_data = matchup_mapping[manager_a_data["matchup_id"]]

        manager_a = roster_id_to_manager[manager_a_data["roster_id"]]
        manager_b = roster_id_to_manager[manager_b_data["roster_id"]]

        _set_individual_manager_week_data(
            year, week, manager_a, manager_a_data, manager_b, manager_b_data
        )
        _set_individual_manager_week_data(
            year, week, manager_b, manager_b_data, manager_a, manager_a_data
        )


def _set_individual_manager_week_data(
    year: int,
    week: int,
    manager: Manager,
    manager_data: dict[str, Any],
    opponent: Manager,
    opponent_data: dict[str, Any],
) -> None:
    """Sets the week data for a manager.

    Args:
        year: The year for which to set the week data.
        week: The week for which to set the week data.
        manager: The manager to set the week data for
        manager_data: The matchup data for the manager
        opponent: The opponent manager
        opponent_data: The matchup data for the opponent
    """
    if manager_data["points"] > opponent_data["points"]:
        result = "win"
    elif manager_data["points"] < opponent_data["points"]:
        result = "loss"
    else:
        result = "tie"

    manager.set_week_data(
        str(year),
        str(week),
        opponent,  # Opponent
        result,  # Result
        manager_data["points"],  # Points for
        opponent_data["points"],  # Points against
        manager_data["starters_objects"],  # Starters
        manager_data["players_objects"],  # Rostered players
    )


# for manager_username in USERNAME_TO_REAL_NAME:
#     fetch_user_metadata(manager_username)

# s = fetch_sleeper_data(f"league/{LEAGUE_IDS[2020]}/users")
# print()
# if __name__ == "__main__":
#     get_roster_id("607421766062637056", 2025)
