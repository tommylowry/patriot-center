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
from patriot_center_backend.cache.updaters.starters_updater import (
    update_starters_cache,
)
from patriot_center_backend.cache.updaters.valid_options_updater import (
    update_valid_options_cache,
)
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.playoffs.playoff_tracker import (
    assign_placements_retroactively,
    get_playoff_roster_ids,
)
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
        if last_updated_season != 0 and last_updated_season < year:
            starters_cache["Last_Updated_Week"] = 0  # Reset for new season

        # Early exit if fully up to date (prevents unnecessary API calls).
        if last_updated_season == current_season:
            if last_updated_week == current_week:
                # Week 17 is the final playoff week; assign final placements if
                # reached.
                if current_week == 17:
                    assign_placements_retroactively(year)

                break

        # For completed seasons, retroactively assign placements if not already
        #   done.
        # Skip the first season in LEAGUE_IDS since it may not have prior data.
        elif year != min(LEAGUE_IDS.keys()):
            assign_placements_retroactively(year - 1)

        year = int(year)
        max_weeks = get_max_weeks(
            year, current_season=current_season, current_week=current_week
        )

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
                assign_placements_retroactively(year)

            starters_cache.setdefault(str(year), {})

            # Initialize new weeks
            starters_cache[str(year)][str(week)] = {}

            # Update all weekly caches
            _cache_week(year, week, manager_updater)

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


def _cache_week(
    season: int,
    week: int,
    manager_updater: ManagerMetadataManager,
) -> None:
    """Fetch starters data for a given week.

    Args:
        season: The NFL season year (e.g., 2024).
        week: The week number (1-17).
        manager_updater: ManagerMetadataManager instance

    Raises:
        ValueError: If the data for the given week is not valid.
    """
    league_id = LEAGUE_IDS[season]

    sleeper_response_matchups = fetch_sleeper_data(
        f"league/{league_id}/matchups/{week}"
    )
    if not isinstance(sleeper_response_matchups, list):
        raise ValueError("Sleeper Matchups return not in list form")

    roster_ids = get_roster_ids(season, week)

    playoff_roster_ids = get_playoff_roster_ids(
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

        if not roster_id_to_matchup.get(roster_id):
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
    """
    for player_id in matchup["starters"]:
        update_valid_options_cache(
            year, week, manager, player_id
        )

        update_players_cache(player_id)

        player_score = matchup["players_points"].get(player_id, 0.0)

        update_starters_cache(
            year, week, manager, player_id, player_score
        )
