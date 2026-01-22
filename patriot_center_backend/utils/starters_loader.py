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
    - Save and reload to remove metadata fields.
    """
    starters_cache = CACHE_MANAGER.get_starters_cache(for_update=True)
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    current_season, current_week = get_current_season_and_week()
    if current_week > 17:
        current_week = 17  # Regular season cap

    for year in LEAGUE_IDS:
        last_updated_season = int(
            starters_cache.get("Last_Updated_Season", "0")
        )
        last_updated_week = starters_cache.get("Last_Updated_Week", 0)

        # Skip previously finished seasons; reset week marker when advancing.
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                starters_cache["Last_Updated_Week"] = 0  # Reset for new season

        # Early exit if fully up to date (prevents unnecessary API calls).
        if last_updated_season == int(current_season):
            if last_updated_week == current_week:
                # Week 17 is the final playoff week; assign placements.
                if current_week == 17:
                    retroactively_assign_team_placement_for_player(year)

                break

        # For completed seasons, retroactively assign
        #   placements if not already done.
        # Skip the first season in LEAGUE_IDS since it will not have prior data.
        elif year != min(LEAGUE_IDS.keys()):
            retroactively_assign_team_placement_for_player(year - 1)

        year = int(year)
        max_weeks = _get_max_weeks(year, int(current_season), current_week)

        if year in (int(current_season), last_updated_season):
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

        if not starters_cache.get(str(year)):
            starters_cache[str(year)] = {}

        if not valid_options_cache.get(str(year)):
            valid_options_cache[str(year)] = {
                "managers": [],
                "players": [],
                "weeks": [],
                "positions": [],
            }

        for week in weeks_to_update:
            starters_cache[str(year)][str(week)] = {}

            valid_options_cache[str(year)][str(week)] = {
                "managers": [],
                "players": [],
                "positions": [],
            }

            # Final week; assign final placements if reached.
            if week == max_weeks:
                retroactively_assign_team_placement_for_player(year)

            cache_starters_for_week(year, week)

            MANAGER_METADATA_MANAGER.cache_week_data(str(year), str(week))

            # Advance progress markers (enables resumable incremental updates).
            starters_cache["Last_Updated_Season"] = str(year)
            starters_cache["Last_Updated_Week"] = week
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


def _get_relevant_playoff_roster_ids(year: int, week: int) -> list[int]:
    """Return relevant playoff roster IDs for the given year and week.

    Relevant_roster_ids is a list of roster IDs relevant to the given week in
    the fantasy playoffs. This list will be empty if the week is not a playoff
    week.

    Args:
        year: The year to get playoff roster IDs for.
        week: The week to get playoff roster IDs for.

    Returns:
        List of relevant playoff roster IDs.

    Raises:
        ValueError: If the week is not a playoff week, or if the week is 17.
    """
    relevant_roster_ids = []

    if (year <= 2020 and week <= 13) or (year >= 2021 and week <= 14):
        return []

    sleeper_response_playoff_bracket = fetch_sleeper_data(
        f"league/{LEAGUE_IDS[year]}/winners_bracket"
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

    for matchup in sleeper_response_playoff_bracket:
        if isinstance(matchup, dict) and matchup.get("r") == round:
            if matchup.get("p") == 5:
                continue  # Skip consolation match
            relevant_roster_ids.append(matchup["t1"])
            relevant_roster_ids.append(matchup["t2"])

    if len(relevant_roster_ids) == 0:
        raise ValueError("Cannot get playoff roster IDs for the given week")

    return relevant_roster_ids


def _get_playoff_placement(year: int) -> dict[str, int]:
    """Get playoff placement for a given year.

    Args:
        year: The year to get playoff placement for.

    Returns:
        Dictionary mapping manager names to playoff placement.

    Raises:
        ValueError: If the API call fails to retrieve playoff bracket,
            rosters, or users in list form.
    """
    league_id = LEAGUE_IDS[int(year)]

    sleeper_response_playoff_bracket = fetch_sleeper_data(
        f"league/{league_id}/winners_bracket"
    )
    sleeper_response_rosters = fetch_sleeper_data(f"league/{league_id}/rosters")
    sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")

    if (
        not isinstance(sleeper_response_playoff_bracket, list)
        or not isinstance(sleeper_response_rosters, list)
        or not isinstance(sleeper_response_users, list)
    ):
        raise ValueError(
            f"Sleeper API call failed to retrieve playoff bracket, "
            f"rosters, or users in list form for year {year}"
        )

    championship = sleeper_response_playoff_bracket[-2]
    third_place = sleeper_response_playoff_bracket[-1]

    placement = {}

    for manager in sleeper_response_users:
        for roster in sleeper_response_rosters:
            if manager["user_id"] == roster["owner_id"]:
                real_name = USERNAME_TO_REAL_NAME[manager["display_name"]]
                if roster["roster_id"] == championship["w"]:
                    placement[real_name] = 1
                if roster["roster_id"] == championship["l"]:
                    placement[real_name] = 2
                if roster["roster_id"] == third_place["w"]:
                    placement[real_name] = 3

    return placement


def cache_starters_for_week(year: int, week: int) -> None:
    """Cache starters data for a given year and week.

    Args:
        year: The year to cache starters data for.
        week: The week to cache starters data for.

    Raises:
        ValueError: If the Sleeper API call fails to retrieve users, rosters, or
            matchups in list form for the given year and week.

    """
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()

    league_id = LEAGUE_IDS[int(year)]

    sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
    sleeper_response_rosters = fetch_sleeper_data(f"league/{league_id}/rosters")
    sleeper_response_matchups = fetch_sleeper_data(
        f"league/{league_id}/matchups/{week}"
    )

    if (
        not isinstance(sleeper_response_users, list)
        or not isinstance(sleeper_response_rosters, list)
        or not isinstance(sleeper_response_matchups, list)
    ):
        raise ValueError(
            f"Sleeper API call failed to retrieve users, rosters, "
            f"or matchups in list form for year {year} and week {week}"
        )

    playoff_roster_ids = _get_relevant_playoff_roster_ids(year, week)

    valid_options_cache[str(year)]["weeks"].append(str(week))

    managers = sleeper_response_users
    for manager in managers:
        if manager["display_name"] not in USERNAME_TO_REAL_NAME:
            raise ValueError(
                f"{manager['display_name']} not "
                f"in {USERNAME_TO_REAL_NAME.keys()}"
            )

        real_name = USERNAME_TO_REAL_NAME[manager["display_name"]]

        # Historical correction: In 2019 weeks 1-3, Tommy played under Cody's
        #   roster.
        # Reassign those weeks from Cody to Tommy for accurate records.
        if year == 2019 and week < 4 and real_name == "Cody":
            real_name = "Tommy"

        roster_id = get_roster_id(
            manager["user_id"],
            year,
            sleeper_rosters_response=sleeper_response_rosters,
        )
        if not roster_id:
            logger.warning(
                f"Could not find roster for {manager['display_name']} "
                f"({manager['user_id']}) in year {year} week {week}"
            )
            continue

        # Initialize manager metadata for this season/week before skipping
        # playoff filtering.
        MANAGER_METADATA_MANAGER.set_roster_id(
            real_name,
            str(year),
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
        if roster_id not in playoff_roster_ids:
            continue  # Skip non-playoff rosters in playoff weeks

        cache_starters_data(
            year, week, sleeper_response_matchups, roster_id, real_name
        )


def cache_starters_data(
    year: int,
    week: int,
    matchups: list[dict[str, Any]],
    roster_id: int,
    manager_name: str,
) -> None:
    """Cache weekly starters data from matchup data.

    Args:
        year: Season year.
        week: Week number.
        matchups: Matchup data from Sleeper API.
        roster_id: Sleeper roster ID for this manager.
        manager_name: Display name for this manager.
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()
    starters_cache = CACHE_MANAGER.get_starters_cache()

    wk_starters = starters_cache[str(year)][str(week)]

    for matchup in matchups:
        if matchup["roster_id"] == roster_id:
            wk_starters[manager_name] = {"Total_Points": 0.0}

            yr_lvl_options = valid_options_cache[str(year)]

            if manager_name not in yr_lvl_options["managers"]:
                yr_lvl_options["managers"].append(manager_name)
            yr_lvl_options[str(week)]["managers"].append(manager_name)

            yr_players = yr_lvl_options["players"]
            yr_positions = yr_lvl_options["positions"]

            wk_players = yr_lvl_options[str(week)]["players"]
            wk_positions = yr_lvl_options[str(week)]["positions"]

            yr_lvl_options[str(week)][manager_name] = {
                "players": [],
                "positions": [],
            }

            mgr_players = yr_lvl_options[str(week)][manager_name]["players"]
            mgr_positions = yr_lvl_options[str(week)][manager_name]["positions"]

            for player_id in matchup["starters"]:
                player_meta = player_ids_cache.get(player_id, {})

                player_name = player_meta.get("full_name")
                if not player_name:
                    continue  # Skip unknown player
                player_position = player_meta.get("position")
                if not player_position:
                    continue  # Skip if no position resolved

                mgr_players.append(player_name)
                mgr_positions.append(player_position)

                wk_players.append(player_name)
                wk_positions.append(player_position)

                if player_name not in yr_players:
                    yr_players.append(player_name)
                if player_position not in yr_positions:
                    yr_positions.append(player_position)

                update_players_cache(player_id)

                player_score = matchup["players_points"].get(player_id, 0.0)

                wk_starters[manager_name][player_name] = {
                    "points": player_score,
                    "position": player_position,
                    "player_id": player_id,
                }

                wk_starters[manager_name]["Total_Points"] += player_score

            wk_starters[manager_name]["Total_Points"] = float(
                Decimal(wk_starters[manager_name]["Total_Points"])
                .quantize(Decimal("0.01"))
                .normalize()
            )
            return

    logger.warning(f"Roster {roster_id} not found in week {week}.")
    return


def retroactively_assign_team_placement_for_player(year: int) -> None:
    """Retroactively assign team placement for a given year.

    Given a year, this function fetches the placements for that year and
    applies them to the manager data structures in the starters cache.

    The function first fetches the placements from the cache, then iterates
    over the weeks of the given year, updating the placements for each
    manager in the starters cache.

    Args:
        year (int): The year for which to assign placements.
    """
    starters_cache = CACHE_MANAGER.get_starters_cache()

    placements = _get_playoff_placement(year)
    if not placements:
        return

    MANAGER_METADATA_MANAGER.set_playoff_placements(placements, str(year))

    weeks = ["15", "16", "17"]
    if year <= 2020:
        weeks = ["14", "15", "16"]

    need_to_print = True
    for week in weeks:
        for manager in starters_cache.get(str(year), {}).get(week, {}):
            if manager in placements:
                manager_lvl = starters_cache[str(year)][week][manager]
                for player in manager_lvl:
                    if player != "Total_Points":
                        # placement already assigned
                        if "placement" in manager_lvl[player]:
                            return

                        if need_to_print:
                            logger.info(
                                f"New placements found: {placements}, "
                                f"retroactively applying placements."
                            )
                            need_to_print = False

                        manager_lvl[player]["placement"] = placements[manager]
