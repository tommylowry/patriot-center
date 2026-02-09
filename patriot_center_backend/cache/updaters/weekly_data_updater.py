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
from patriot_center_backend.cache.updaters.manager_data_updater import (
    ManagerMetadataManager,
)
from patriot_center_backend.cache.updaters.replacement_score_updater import (
    ReplacementScoreCacheBuilder,
)
from patriot_center_backend.calculations.ffwar_calculator import FFWARCalculator
from patriot_center_backend.constants import LEAGUE_IDS
from patriot_center_backend.playoffs.playoff_tracker import (
    assign_placements_retroactively,
)
from patriot_center_backend.utils.sleeper_helpers import (
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
    manager_updater = ManagerMetadataManager()

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

            manager_updater.cache_week_data(str(year), str(week))
            FFWARCalculator(year, week).calculate_and_set_ffwar_for_week()

            # Assign playoff placements
            if week == max(weeks_to_update) and season_complete:
                assign_placements_retroactively(year)

            log_cache_update(year, week, "Weekly Data")

            set_last_updated(year, week)

    CACHE_MANAGER.save_all_caches()
