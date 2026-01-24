"""Cache update orchestration.

Single entry point for all cache updates. Runs updates in dependency order:
1. player_ids - Sleeper player metadata (external API)
2. weekly_data - starters, valid_options, players, manager_data, transaction_ids
3. replacement_score - position replacement scores
4. player_data - ffWAR calculations
"""

import logging

from patriot_center_backend.cache.updaters.player_data_updater import (
    update_player_data_cache,
)
from patriot_center_backend.cache.updaters.player_ids_updater import (
    update_player_ids_cache,
)
from patriot_center_backend.cache.updaters.replacement_score_updater import (
    update_replacement_score_cache,
)
from patriot_center_backend.cache.updaters.weekly_data_updater import (
    update_weekly_data_caches,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def update_all_caches() -> None:
    """Run all cache updates in dependency order."""
    update_player_ids_cache()         # Step 1
    update_weekly_data_caches()       # Step 2
    update_replacement_score_cache()  # Step 3
    update_player_data_cache()        # Step 4
