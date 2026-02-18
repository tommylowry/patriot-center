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

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters._base import log_cache_update
from patriot_center_backend.cache.updaters._progress_tracker import (
    get_league_status,
    set_last_updated,
)
from patriot_center_backend.cache.updaters.replacement_score_updater import (
    ReplacementScoreCacheBuilder,
)
from patriot_center_backend.cache.updaters.transaction_processor import (
    update_transactions,
)
from patriot_center_backend.calculations.ffwar_calculator import FFWARCalculator
from patriot_center_backend.calculations.player_score_calculator import (
    calculate_player_score,
)
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.models import Player
from patriot_center_backend.playoffs.playoff_tracker import (
    assign_placements_retroactively,
)
from patriot_center_backend.utils.sleeper_helpers import (
    fetch_sleeper_data,
    set_managers_season_data,
    set_matchup_data,
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
    for year in LEAGUE_IDS:
        ReplacementScoreCacheBuilder(year).update()

        weeks_to_update, season_complete = get_league_status(year)

        if not weeks_to_update:
            continue

        logger.info(
            f"Updating weekly data caches for season "
            f"{year}, weeks: {weeks_to_update}"
        )

        for week in weeks_to_update:
            managers = set_managers_season_data(year, week)
            set_matchup_data(year, week, managers=managers)

            players = _apply_player_data_to_week(year, week)
            FFWARCalculator(year, week).calculate_and_set_ffwar_for_week(
                players
            )

            update_transactions(year, week)

            # Assign playoff placements
            if week == max(weeks_to_update) and season_complete:
                assign_placements_retroactively(year)

            log_cache_update(year, week, "Weekly Data")
            set_last_updated(year, week)

    CACHE_MANAGER.save_all_caches()


def _apply_player_data_to_week(year: int, week: int) -> list[Player]:
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

    for player_id in week_data:
        if "TEAM_" in player_id:
            continue

        player = Player(player_id)
        if not player._is_real_player:
            continue

        points = calculate_player_score(week_data[player_id], scoring_settings)
        player.set_week_data(str(year), str(week), points=points)

        players.append(player)

    return players
