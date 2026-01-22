"""Starters cache builder/updater for Patriot Center.

Responsibilities:
- Maintain per-week starters and points per manager from Sleeper.
- Incrementally update a JSON cache, resuming from Last_Updated_* markers.
- Normalize totals to 2 decimals and resolve manager display names.

Performance:
- Minimizes API calls by:
  * Skipping already processed weeks (progress markers).
  * Only fetching week/user/roster/matchup data when needed.

Notes:
- Weeks are capped at 17 to include fantasy playoffs.
- Import-time execution at bottom warms the cache for downstream consumers.
"""

import logging
from copy import deepcopy
from decimal import Decimal
from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME
from patriot_center_backend.managers import MANAGER_METADATA_MANAGER
from patriot_center_backend.utils.player_cache_updater import (
    update_players_cache,
)
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
    get_current_season_and_week,
    get_roster_id,
)

logger = logging.getLogger(__name__)


def update_starters_cache() -> None:
    """Incrementally load/update starters cache and persist changes.

    Logic:
    - Resume from Last_Updated_* markers (avoids redundant API calls).
    - Cap weeks at 17 (include playoffs).
    - Only fetch missing weeks per season; break early if fully current.
    - Strip metadata before returning to callers.
    """
    starters_cache = CACHE_MANAGER.get_starters_cache(for_update=True)
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    current_season, current_week = get_current_season_and_week()
    if current_week > 17:
        current_week = 17  # Regular season cap

    for year in LEAGUE_IDS:
        last_updated_season = int(
            starters_cache.get("Last_Updated_Season", '0')
        )
        last_updated_week = starters_cache.get("Last_Updated_Week", 0)

        # Skip previously finished seasons; reset week marker when advancing
        # season.
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                starters_cache['Last_Updated_Week'] = 0  # Reset for new season

        # Early exit if fully up to date (prevents unnecessary API calls).
        if last_updated_season == current_season:
            if last_updated_week == current_week:

                # Week 17 is the final playoff week; assign final placements if
                # reached.
                if current_week == 17:
                    retroactively_assign_team_placement_for_player(year)

                break

        # For completed seasons, retroactively assign placements if not already
        #   done.
        # Skip the first season in LEAGUE_IDS since it may not have prior data.
        elif year != min(LEAGUE_IDS.keys()):
            retroactively_assign_team_placement_for_player(year - 1)

        year = int(year)
        max_weeks = _get_max_weeks(year, current_season, current_week)

        if year in (current_season, last_updated_season):
            last_updated_week = starters_cache.get("Last_Updated_Week", 0)
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)

        if not weeks_to_update:
            continue

        logger.info(
            f"Updating starters cache for season "
            f"{year}, weeks: {list(weeks_to_update)}"
        )

        for week in weeks_to_update:

            # Final week; assign final placements if reached.
            if week == max_weeks:
                retroactively_assign_team_placement_for_player(year)

            starters_cache.setdefault(str(year), {})
            valid_options_cache.setdefault(str(year), {})

            managers = valid_options_cache[str(year)].get("managers", [])
            players = valid_options_cache[str(year)].get("players", [])
            weeks = list(valid_options_cache[str(year)].keys())
            for key in deepcopy(weeks):
                if not key.isdigit():
                    weeks.remove(key)
            positions = valid_options_cache[str(year)].get("positions", [])

            (
                week_data,
                weekly_managers_summary_array,
                weekly_players_summary_array,
                weekly_positions_summary_array,
                week_valid_data,
            ) = fetch_starters_for_week(year, week)

            for weekly_manager in weekly_managers_summary_array:
                if weekly_manager not in managers:
                    managers.append(weekly_manager)
            for weekly_player in weekly_players_summary_array:
                if weekly_player not in players:
                    players.append(weekly_player)
            for weekly_position in weekly_positions_summary_array:
                if weekly_position not in positions:
                    positions.append(weekly_position)

            weeks.append(str(week))

            valid_options_cache[str(year)]["managers"] = managers
            valid_options_cache[str(year)]["players"] = players
            valid_options_cache[str(year)]["weeks"] = weeks
            valid_options_cache[str(year)]["positions"] = positions
            valid_options_cache[str(year)][str(week)] = week_valid_data

            starters_cache[str(year)][str(week)] = week_data

            MANAGER_METADATA_MANAGER.cache_week_data(str(year), str(week))

            # Advance progress markers (enables resumable incremental updates).
            starters_cache['Last_Updated_Season'] = str(year)
            starters_cache['Last_Updated_Week'] = week
            logger.info(
                f"\tStarters cache updated internally "
                f"for season {year}, week {week}"
            )


    CACHE_MANAGER.save_all_caches()

    # Reload to remove the metadata fields
    CACHE_MANAGER.get_starters_cache(force_reload=True)

def _get_max_weeks(season: int, current_season: int, current_week: int) -> int:
    """Determine maximum playable weeks for a season.

    Rules:
    - Live season -> current_week.
    - 2019/2020 -> 16 (legacy rule set).
    - Other seasons -> 17 (regular season boundary).

    Args:
        season: The season to determine the max weeks for.
        current_season: The current season.
        current_week: The current week.

    Returns:
        Max week to process for season.
    """
    if season == current_season:
        return current_week
    elif season in [2019, 2020]:
        return 16
    return 17

def _get_relevant_playoff_roster_ids(
    season: int, week: int, league_id: str
) -> list[int]:
    """Determine which rosters are participating in playoffs for a given week.

    Filters out regular season weeks and consolation bracket teams,
    returning only the roster IDs competing in the winners bracket.

    Rules:
    - 2019/2020: Playoffs start week 14 (rounds 1-3 for weeks 14-16).
    - 2021+: Playoffs start week 15 (rounds 1-3 for weeks 15-17).
    - Week 17 in 2019/2020 (round 4) is unsupported and raises an error.
    - Consolation bracket matchups (p=5) are excluded.

    Args:
        season (int): Target season year.
        week (int): Target week number.
        league_id (str): Sleeper league identifier.

    Returns:
        [int] or [] if regular season week.
              Empty dict signals no playoff filtering needed.

    Raises:
        ValueError: If week 17 in 2019/2020 or no rosters found for the round.
    """
    if int(season) <= 2020 and week <= 13:
        return []
    if int(season) >= 2021 and week <= 14:
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

    if season >= 2021:
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
            relevant_roster_ids.append(matchup['t1'])
            relevant_roster_ids.append(matchup['t2'])

    if len(relevant_roster_ids) == 0:
        raise ValueError("Cannot get playoff roster IDs for the given week")

    return relevant_roster_ids

def _get_playoff_placement(season: int) -> dict[str, int]:
    """Retrieve final playoff placements (1st, 2nd, 3rd) for a completed season.

    Fetches the winners bracket from Sleeper API and determines:
    - 1st place: Winner of championship match (last-1 matchup winner)
    - 2nd place: Loser of championship match
    - 3rd place: Winner of 3rd place match (last matchup winner)

    Args:
        season: Target season year (must be completed).

    Returns:
        Dict of keys (manager names) and values (placement) or empty dict if
        season is not completed.
    """
    league_id = LEAGUE_IDS[int(season)]

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
            if manager['user_id'] == roster['owner_id']:
                manager_name = USERNAME_TO_REAL_NAME[manager['display_name']]
                if roster['roster_id'] == championship['w']:
                    placement[manager_name] = 1
                elif roster['roster_id'] == championship['l']:
                    placement[manager_name] = 2
                elif roster['roster_id'] == third_place['w']:
                    placement[manager_name] = 3

    return placement


def fetch_starters_for_week(
    season: int, week: int) -> tuple[
    dict[str, Any], list[str], list[str], list[str], dict[str, list[str]]
]:
    """Fetch starters data for a given week.

    Args:
        season: The NFL season year (e.g., 2024).
        week: The week number (1-17).

    Returns:
        tuple:
            - A dictionary containing the starters data for the given week.
            - A list of manager names that have valid data for the given week.
            - A list of player names that are valid for the given week.
            - A list of position names that are valid for the given week.
            - A dictionary containing the valid data for the given week.

    Raises:
        ValueError: If the data for the given week is not valid.
    """
    league_id = LEAGUE_IDS[season]

    sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
    sleeper_response_rosters = fetch_sleeper_data(f"league/{league_id}/rosters")
    sleeper_response_matchups = fetch_sleeper_data(
        f"league/{league_id}/matchups/{week}"
    )

    if not isinstance(sleeper_response_users, list):
        raise ValueError("Sleeper Users return not in list form")
    if not isinstance(sleeper_response_rosters, list):
        raise ValueError("Sleeper Rosters return not in list form")
    if not isinstance(sleeper_response_matchups, list):
        raise ValueError("Sleeper Matchups return not in list form")

    playoff_roster_ids = _get_relevant_playoff_roster_ids(
        season, week, league_id
    )

    managers_summary_array = []
    players_summary_array = []
    positions_summary_array = []
    week_valid_data = {}

    managers = sleeper_response_users
    week_data = {}
    for manager in managers:
        players_summary_array_per_manager = []
        positions_summary_array_per_manager = []

        if manager['display_name'] not in USERNAME_TO_REAL_NAME:
            raise ValueError(
                f"{manager['display_name']} not "
                f"in {USERNAME_TO_REAL_NAME.keys()}"
            )

        real_name = USERNAME_TO_REAL_NAME[manager['display_name']]

        # Historical correction: In 2019 weeks 1-3, Tommy played then
        #   Cody took over
        # Reassign those weeks from Cody to Tommy for accurate records.
        if season == 2019 and week < 4 and real_name == "Cody":
            real_name = "Tommy"

        roster_id = get_roster_id(
            manager['user_id'],
            season,
            sleeper_rosters_response=sleeper_response_rosters
        )

        if not roster_id:
            continue

        # Initialize manager metadata for this season/week before skipping
        # playoff filtering.
        MANAGER_METADATA_MANAGER.set_roster_id(
            real_name,
            str(season),
            str(week),
            roster_id,
            playoff_roster_ids,
            sleeper_response_matchups,
        )

        if not roster_id:
            continue  # Skip unresolved roster

        # During playoff weeks, only include rosters actively competing in that
        #   round.
        # This filters out teams eliminated or in consolation bracket.
        if playoff_roster_ids != {} and roster_id not in playoff_roster_ids:
            continue  # Skip non-playoff rosters in playoff weeks

        (
            starters_data,
            players_summary_array_per_manager,
            positions_summary_array_per_manager,
        ) = get_starters_data(
            sleeper_response_matchups,
            roster_id,
            players_summary_array_per_manager,
            positions_summary_array_per_manager,
        )
        if starters_data:
            week_data[real_name] = starters_data
            week_valid_data[real_name] = {
                "players": players_summary_array_per_manager,
                "positions": positions_summary_array_per_manager,
            }

            managers_summary_array.append(real_name)
            for player in players_summary_array_per_manager:
                if player not in players_summary_array:
                    players_summary_array.append(player)
            for position in positions_summary_array_per_manager:
                if position not in positions_summary_array:
                    positions_summary_array.append(position)

    week_valid_data["managers"] = managers_summary_array
    week_valid_data["players"] = players_summary_array
    week_valid_data["positions"] = positions_summary_array

    return (
        week_data,
        managers_summary_array,
        players_summary_array,
        positions_summary_array,
        week_valid_data
    )

def get_starters_data(
    matchups: list[dict[str, Any]],
    roster_id: int,
    players_summary_array: list[str],
    positions_summary_array: list[str],
) -> tuple[dict[str, float | dict[str, str | float]], list[str], list[str]]:
    """Get starters data for a given manager and week.

    Args:
        matchups: List of matchup data from Sleeper API.
        roster_id: The roster ID of the manager.
        players_summary_array: List of player names.
        positions_summary_array: List of position names.

    Returns:
        tuple:
            - A dictionary containing the starters data for the given manager
                and week.
            - A list of player names that are valid for the given week.
            - A list of position names that are valid for the given week.

    Raises:
        Exception: If total points somehow isn't a float.
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    for matchup in matchups:
        if matchup['roster_id'] == roster_id:
            manager_data: dict[str, float | dict[str, str | float]] = {
                "Total_Points": 0.0,
            }
            for player_id in matchup['starters']:

                player_meta = player_ids_cache.get(player_id, {})

                player_name = player_meta.get('full_name')
                if not player_name:
                    continue  # Skip unknown player
                player_position = player_meta.get('position')
                if not player_position:
                    continue  # Skip if no position resolved

                if player_name not in players_summary_array:
                    players_summary_array.append(player_name)
                if player_position not in positions_summary_array:
                    positions_summary_array.append(player_position)

                update_players_cache(player_id)

                player_score = matchup['players_points'].get(player_id, 0)

                manager_data[player_name] = {
                    "points": player_score,
                    "position": player_position,
                    "player_id": player_id
                }

                manager_data["Total_Points"] += player_score

            if not isinstance(manager_data["Total_Points"], float):
                raise Exception("Non-float found in Total_Points")

            manager_data["Total_Points"] = float(
                Decimal(
                    manager_data["Total_Points"]
                ).quantize(Decimal('0.01')).normalize()
            )
            return manager_data, players_summary_array, positions_summary_array
    return {}, players_summary_array, positions_summary_array


def retroactively_assign_team_placement_for_player(season: int) -> None:
    """Retroactively assign team placement for a given season.

    Args:
        season: Season year (e.g., 2024)

    Notes:
        - Fetches placements from _get_playoff_placement
        - Updates manager metadata with new placements
        - Iterates over starters cache and assigns placements for each manager
        - Only logs the first occurrence of a season's placements
    """
    starters_cache = CACHE_MANAGER.get_starters_cache()

    placements = _get_playoff_placement(season)
    if not placements:
        return

    MANAGER_METADATA_MANAGER.set_playoff_placements(placements, str(season))

    weeks = ['15', '16', '17']
    if season <= 2020:
        weeks = ['14', '15', '16']

    need_to_log = True
    season_str = str(season)
    for week in weeks:
        for manager in starters_cache.get(season_str, {}).get(week, {}):
            if manager in placements:
                manager_lvl = starters_cache[season_str][week][manager]
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

                        manager_lvl[player]['placement'] = placements[manager]
