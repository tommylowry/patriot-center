"""Functions for tracking playoff progress and results."""

import logging

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters.manager_data_updater import (
    ManagerMetadataManager,
)
from patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME
from patriot_center_backend.utils.sleeper_helpers import fetch_sleeper_data

logger = logging.getLogger(__name__)


def get_playoff_roster_ids(
    year: int, week: int, league_id: str
) -> list[int]:
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
        league_id (str): Sleeper league identifier.

    Returns:
        [int] or [] if regular year week.
              Empty dict signals no playoff filtering needed.

    Raises:
        ValueError: If week 17 in 2019/2020 or no rosters found for the round.
    """
    if int(year) <= 2020 and week <= 13:
        return []
    if int(year) >= 2021 and week <= 14:
        return []

    sleeper_response_playoff_bracket = fetch_sleeper_data(
        f"league/{league_id}/winners_bracket"
    )

    if week == 14:
        round = 1
    elif week == 15:
        round = 2
    elif week == 16:
        round = 3
    else:
        round = 4

    if year >= 2021:
        round -= 1

    if round == 4:
        raise ValueError("Cannot get playoff roster IDs for week 17")
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


def get_playoff_placements(year: int) -> dict[str, int]:
    """Retrieve final playoff placements (1st, 2nd, 3rd) for a completed year.

    Fetches the winners bracket from Sleeper API and determines:
    - 1st place: Winner of championship match (last-1 matchup winner)
    - 2nd place: Loser of championship match
    - 3rd place: Winner of 3rd place match (last matchup winner)

    Args:
        year: Target year year (must be completed).

    Returns:
        Dict of keys (manager names) and values (placement) or empty dict if
        year is not completed.
    """
    league_id = LEAGUE_IDS[int(year)]

    sleeper_response_playoff_bracket = fetch_sleeper_data(
        f"league/{league_id}/winners_bracket"
    )
    sleeper_response_rosters = fetch_sleeper_data(f"league/{league_id}/rosters")
    sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")

    if not isinstance(sleeper_response_playoff_bracket, list):
        logger.warning("Sleeper Playoff Bracket return not in list form")
        return {}
    if not isinstance(sleeper_response_rosters, list):
        logger.warning("Sleeper Rosters return not in list form")
        return {}
    if not isinstance(sleeper_response_users, list):
        logger.warning("Sleeper Users return not in list form")
        return {}

    championship = sleeper_response_playoff_bracket[-2]
    third_place = sleeper_response_playoff_bracket[-1]

    placement = {}

    for manager in sleeper_response_users:
        for roster in sleeper_response_rosters:
            if manager["user_id"] == roster["owner_id"]:
                manager_name = USERNAME_TO_REAL_NAME[manager["display_name"]]
                if roster["roster_id"] == championship["w"]:
                    placement[manager_name] = 1
                elif roster["roster_id"] == championship["l"]:
                    placement[manager_name] = 2
                elif roster["roster_id"] == third_place["w"]:
                    placement[manager_name] = 3

    return placement


def assign_placements_retroactively(year: int) -> None:
    """Retroactively assign team placement for a given year.

    Args:
        year: Season year (e.g., 2024)

    Notes:
        - Fetches placements from get_playoff_placements
        - Updates manager metadata with new placements
        - Iterates over starters cache and assigns placements for each manager
        - Only logs the first occurrence of a year's placements
    """
    starters_cache = CACHE_MANAGER.get_starters_cache()

    placements = get_playoff_placements(year)
    if not placements:
        return

    manager_updater = ManagerMetadataManager()
    manager_updater.set_playoff_placements(placements, str(year))

    weeks = ["15", "16", "17"]
    if year <= 2020:
        weeks = ["14", "15", "16"]

    need_to_log = True
    year_str = str(year)
    for week in weeks:
        for manager in starters_cache.get(year_str, {}).get(week, {}):
            if manager in placements:
                manager_lvl = starters_cache[year_str][week][manager]
                for player in manager_lvl:
                    if player != "Total_Points":
                        # placement already assigned
                        if "placement" in manager_lvl[player]:
                            return

                        if need_to_log:
                            logger.info(
                                f"New placements found: {placements}, "
                                f"retroactively applying placements."
                            )
                            need_to_log = False

                        manager_lvl[player]["placement"] = placements[manager]
