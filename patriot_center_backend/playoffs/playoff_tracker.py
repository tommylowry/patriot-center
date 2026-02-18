"""Functions for tracking playoff progress and results."""

import logging

from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.models import Manager, Player
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
    get_playoff_weeks,
    get_roster_ids_map,
)

logger = logging.getLogger(__name__)


def assign_placements_retroactively(year: int) -> None:
    """Retrieve final playoff placements (1st, 2nd, 3rd) for a completed year.

    Fetches the winners bracket from Sleeper API and determines:
    - 1st place: Winner of championship match (last-1 matchup winner)
    - 2nd place: Loser of championship match
    - 3rd place: Winner of 3rd place match (last matchup winner)

    Args:
        year: Target year year (must be completed).
    """
    sleeper_response_playoff_bracket = fetch_sleeper_data(
        f"league/{LEAGUE_IDS[year]}/winners_bracket"
    )
    if (
        not isinstance(sleeper_response_playoff_bracket, list)
        or not sleeper_response_playoff_bracket
    ):
        return

    championship = sleeper_response_playoff_bracket[-2]
    third_place = sleeper_response_playoff_bracket[-1]
    if championship.get("w") is None:
        return

    weeks: list[int] = get_playoff_weeks(year)
    roster_ids_map: dict[int, Manager] = get_roster_ids_map(
        year, weeks[-1]  # Last week of playoffs
    )

    first_place_manager = roster_ids_map[championship["w"]]
    second_place_manager = roster_ids_map[championship["l"]]
    third_place_manager = roster_ids_map[third_place["w"]]

    logger.info("Assigning playoff placements")

    for cnt, manager in enumerate(
        [first_place_manager, second_place_manager, third_place_manager],
        start=1,
    ):
        logger.info(f"{cnt}. {manager.real_name} ({manager.user_id})")
        manager.set_playoff_placement(str(year), cnt)
        _assign_player_placements(year, weeks, manager, cnt)


def _assign_player_placements(
    year: int, playoff_weeks: list[int], manager: Manager, placement: int
) -> None:
    """Assign player placement for a given manager.

    Args:
        year: The year.
        playoff_weeks: The playoff weeks.
        manager: The manager.
        placement: The placement.
    """
    # Get all starters for the manager in the playoff weeks
    players: list[Player] = []
    for week in playoff_weeks:
        players.extend(
            manager.get_players(
                str(year),
                str(week),
                only_starters=True,
                suppress_warnings=True,
            )
        )

    for player in players:
        player.set_placement(
            str(year), manager, placement
        )
