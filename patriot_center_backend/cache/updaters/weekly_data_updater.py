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
from patriot_center_backend.cache.updaters._base import get_max_weeks
from patriot_center_backend.cache.updaters.manager_data_updater import (
    ManagerMetadataManager,
)
from patriot_center_backend.cache.updaters.player_cache_updater import (
    update_players_cache,
)
from patriot_center_backend.cache.updaters.player_data_updater import (
    update_player_data_cache,
)
from patriot_center_backend.cache.updaters.replacement_score_updater import (
    update_replacement_score_cache,
)
from patriot_center_backend.constants import LEAGUE_IDS, USERNAME_TO_REAL_NAME
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
    get_current_season_and_week,
    get_roster_ids,
)

logger = logging.getLogger(__name__)


def update_weekly_data_caches() -> None:
    """Incrementally load/update starters cache and persist changes.

    Logic:
    - Resume from Last_Updated_* markers (avoids redundant API calls).
    - Cap weeks at 17 (include playoffs).
    - Only fetch missing weeks per season; break early if fully current.
    - Strip metadata before returning to callers.
    """
    starters_cache = CACHE_MANAGER.get_starters_cache(for_update=True)
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()
    replacement_score_cache = CACHE_MANAGER.get_replacement_score_cache()

    manager_updater = ManagerMetadataManager()

    current_season, current_week = get_current_season_and_week()
    if current_week > 17:
        current_week = 17  # Regular season cap

        # Update replacement scores for next week if needed
        current_season_dict = replacement_score_cache.get(str(current_season))
        if (
            current_season_dict
            and str(current_week) in current_season_dict
            and str(current_week + 1) not in current_season_dict
        ):
            update_replacement_score_cache(current_season, current_week + 1)

    for year in LEAGUE_IDS:
        last_updated_season = int(
            starters_cache.get("Last_Updated_Season", "0")
        )
        last_updated_week = starters_cache.get("Last_Updated_Week", 0)

        # Skip previously finished seasons; reset week marker when advancing
        # season.
        if last_updated_season != 0:
            if year < last_updated_season:
                continue
            if last_updated_season < year:
                starters_cache["Last_Updated_Week"] = 0  # Reset for new season

        # Early exit if fully up to date (prevents unnecessary API calls).
        if last_updated_season == current_season:
            if last_updated_week == current_week:
                # Week 17 is the final playoff week; assign final placements if
                # reached.
                if current_week == 17:
                    retroactively_assign_team_placement_for_player(
                        year, manager_updater
                    )

                break

        # For completed seasons, retroactively assign placements if not already
        #   done.
        # Skip the first season in LEAGUE_IDS since it may not have prior data.
        elif year != min(LEAGUE_IDS.keys()):
            retroactively_assign_team_placement_for_player(
                year - 1, manager_updater
            )

        year = int(year)
        max_weeks = get_max_weeks(
            year,
            current_season=current_season,
            current_week=current_week
        )

        if year in (current_season, last_updated_season):
            last_updated_week = starters_cache.get("Last_Updated_Week", 0)
            weeks_to_update = range(last_updated_week + 1, max_weeks + 1)
        else:
            weeks_to_update = range(1, max_weeks + 1)

        if not weeks_to_update:
            continue

        roster_ids = get_roster_ids(year)

        logger.info(
            f"Updating starters cache for season "
            f"{year}, weeks: {list(weeks_to_update)}"
        )

        for week in weeks_to_update:
            # Final week; assign final placements if reached.
            if week == max_weeks:
                retroactively_assign_team_placement_for_player(
                    year, manager_updater
                )

            starters_cache.setdefault(str(year), {})
            valid_options_cache.setdefault(
                str(year),
                {"managers": [], "players": [], "weeks": [], "positions": []}
            )

            # Initialize new weeks
            starters_cache[str(year)][str(week)] = {}
            valid_options_cache[str(year)]["weeks"].append(str(week))
            valid_options_cache[str(year)][str(week)] = {
                "managers": [], "players": [], "positions": []
            }

            # Update all weekly caches
            _cache_week(year, week, manager_updater, roster_ids)

            # Advance progress markers (enables resumable incremental updates).
            starters_cache["Last_Updated_Season"] = str(year)
            starters_cache["Last_Updated_Week"] = week
            logger.info(
                f"\tSeason {year}, Week {week}: Starters Cache Updated."
            )

            if week == max_weeks:
                update_replacement_score_cache(year, week + 1)

    CACHE_MANAGER.save_all_caches()

    # Reload to remove the metadata fields
    CACHE_MANAGER.get_starters_cache(force_reload=True)


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
            relevant_roster_ids.append(matchup["t1"])
            relevant_roster_ids.append(matchup["t2"])

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
            if manager["user_id"] == roster["owner_id"]:
                manager_name = USERNAME_TO_REAL_NAME[manager["display_name"]]
                if roster["roster_id"] == championship["w"]:
                    placement[manager_name] = 1
                elif roster["roster_id"] == championship["l"]:
                    placement[manager_name] = 2
                elif roster["roster_id"] == third_place["w"]:
                    placement[manager_name] = 3

    return placement


def _cache_week(
    season: int,
    week: int,
    manager_updater: ManagerMetadataManager,
    roster_ids: dict[int, str]
) -> None:
    """Fetch starters data for a given week.

    Args:
        season: The NFL season year (e.g., 2024).
        week: The week number (1-17).
        manager_updater: ManagerMetadataManager instance
        roster_ids: Dict of {roster_id: manager_name}

    Raises:
        ValueError: If the data for the given week is not valid.
    """
    league_id = LEAGUE_IDS[season]

    sleeper_response_matchups = fetch_sleeper_data(
        f"league/{league_id}/matchups/{week}"
    )
    if not isinstance(sleeper_response_matchups, list):
        raise ValueError("Sleeper Matchups return not in list form")

    playoff_roster_ids = _get_relevant_playoff_roster_ids(
        season, week, league_id
    )

    roster_id_to_matchup = {}
    for matchup in sleeper_response_matchups:
        if matchup["roster_id"] in roster_ids:
            roster_id_to_matchup[matchup["roster_id"]] = matchup
        else:
            logger.warning(
                f"Roster ID {matchup['roster_id']} in "
                f"matchup not found in inputted roster IDs"
            )

    for roster_id in roster_ids:

        manager_name = roster_ids[roster_id]

        # Historical correction: In 2019 weeks 1-3, Tommy played then
        #   Cody took over
        # Reassign those weeks from Cody to Tommy for accurate records.
        if season == 2019 and week < 4 and manager_name == "Cody":
            manager_name = "Tommy"

        if not roster_id:
            continue

        # Initialize manager data cache updater for this season/week before
        # skipping playoff filtering.
        manager_updater.set_roster_id(
            manager_name,
            str(season),
            str(week),
            roster_id,
            playoff_roster_ids,
            sleeper_response_matchups,
        )

        # During playoff weeks, only include rosters actively competing in that
        #   round.
        # This filters out teams eliminated or in consolation bracket.
        if playoff_roster_ids != [] and roster_id not in playoff_roster_ids:
            continue  # Skip non-playoff rosters in playoff weeks

        if not matchup:
            continue

        # Add matchup data to cache
        _cache_matchup_data(
            str(season),
            str(week),
            roster_id_to_matchup[roster_id],
            manager_name,
        )

    manager_updater.cache_week_data(str(season), str(week))
    update_replacement_score_cache(season, week)
    update_player_data_cache(season, week, roster_ids)


def _cache_matchup_data(
    year: str, week: str, matchup: dict[str, Any], manager: str
) -> None:
    """Update cache with matchup data.

    Args:
        year: The NFL season year (e.g., 2024).
        week: The week number (1-17).
        matchup: Matchup data from Sleeper API.
        manager: Manager name

    Raises:
        Exception: If the total points for the given week is not valid.
    """
    starters_cache = CACHE_MANAGER.get_starters_cache()
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()


    manager_data: dict[str, float | dict[str, str | float]] = {
        "Total_Points": 0.0,
    }
    for player_id in matchup["starters"]:
        player_meta = player_ids_cache.get(player_id, {})

        player_name = player_meta.get("full_name")
        if not player_name:
            continue  # Skip unknown player
        player_position = player_meta.get("position")
        if not player_position:
            continue  # Skip if no position resolved

        _cache_valid_data(
            year, week, manager, player_name, player_position
        )

        update_players_cache(player_id)

        player_score = matchup["players_points"].get(player_id, 0.0)

        manager_data[player_name] = {
            "points": player_score,
            "position": player_position,
            "player_id": player_id,
        }

        manager_data["Total_Points"] += player_score

    if not isinstance(manager_data["Total_Points"], float):
        raise Exception("Non-float found in Total_Points")

    manager_data["Total_Points"] = float(
        Decimal(manager_data["Total_Points"])
        .quantize(Decimal("0.01"))
        .normalize()
    )

    starters_cache[year][week][manager] = manager_data

def _cache_valid_data(
    year: str, week: str, manager: str, player: str, position: str
) -> None:
    """Update cache with valid data.

    Args:
        year: The NFL season year (e.g., 2024).
        week: The week number (1-17).
        manager: Manager name
        player: Player name
        position: Player position
    """
    valid_options_cache = CACHE_MANAGER.get_valid_options_cache()


    year_lvl = valid_options_cache[year]
    if manager not in year_lvl.get("managers", []):
        year_lvl["managers"].append(manager)

    week_lvl = year_lvl[week]
    if manager not in week_lvl.get("managers", []):
        week_lvl["managers"].append(manager)

    mgr_lvl = week_lvl.get(manager, {})
    if not mgr_lvl:
        mgr_lvl = {"players": [], "positions": []}
        week_lvl[manager] = mgr_lvl


    # Add the player and position to the appropriate level
    for lvl in [mgr_lvl, week_lvl, year_lvl]:
        if player not in lvl.get("players", []):
            lvl["players"].append(player)
        if position not in lvl.get("positions", []):
            lvl["positions"].append(position)


def retroactively_assign_team_placement_for_player(
    season: int, manager_updater: ManagerMetadataManager
) -> None:
    """Retroactively assign team placement for a given season.

    Args:
        season: Season year (e.g., 2024)
        manager_updater: ManagerMetadataManager instance

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

    manager_updater.set_playoff_placements(placements, str(season))

    weeks = ["15", "16", "17"]
    if season <= 2020:
        weeks = ["14", "15", "16"]

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

                        manager_lvl[player]["placement"] = placements[manager]
