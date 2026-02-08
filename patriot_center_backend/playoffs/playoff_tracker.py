"""Functions for tracking playoff progress and results."""

import logging

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME
from patriot_center_backend.models import Player
from patriot_center_backend.utils.sleeper_helpers import fetch_sleeper_data

logger = logging.getLogger(__name__)


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
    sleeper_response_playoff_bracket = fetch_sleeper_data(
        f"league/{LEAGUE_IDS[year]}/winners_bracket"
    )
    sleeper_response_rosters = fetch_sleeper_data(
        f"league/{LEAGUE_IDS[year]}/rosters"
    )
    sleeper_response_users = fetch_sleeper_data(
        f"league/{LEAGUE_IDS[year]}/users"
    )

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

    _manager_cache_set_playoff_placements(placements, year)

    weeks = ["15", "16", "17"]
    if year <= 2020:
        weeks = ["14", "15", "16"]

    need_to_log = True
    year_str = str(year)
    for week in weeks:
        for manager in starters_cache.get(year_str, {}).get(week, {}):
            if manager in placements:
                manager_lvl = starters_cache[year_str][week][manager]
                for player_id in manager_lvl:
                    if player_id == "Total_Points":
                        continue

                    player = Player(player_id)
                    player.set_week_data(
                        year_str,
                        week,
                        playoff_placement=placements[manager],
                    )

                    # placement already assigned
                    if "placement" in manager_lvl[str(player)]:
                        return

                    if need_to_log:
                        logger.info(
                            f"New placements found: {placements}, "
                            f"retroactively applying placements."
                        )
                        need_to_log = False

                    manager_lvl[str(player)]["placement"] = placements[manager]


def _manager_cache_set_playoff_placements(
    placement_dict: dict[str, int], year: int
) -> None:
    """Record final season placements for all managers.

    Should be called after season completion to record final standings.
    Only sets placement if not already set for the year (prevents
    overwrites).

    Args:
        placement_dict: Dict mapping manager names to placement
            {"Tommy: 1, "Mike": 2, "Bob": 3}
        year: Season year
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    for manager in placement_dict:
        if manager not in manager_cache:
            continue

        cache_placements = manager_cache[manager]["summary"]["overall_data"][
            "placement"
        ]
        if str(year) not in cache_placements:
            cache_placements[str(year)] = placement_dict[manager]
