"""Cache update orchestration.

Single entry point for all cache updates. Runs updates in dependency order:
1. player_ids - Sleeper player metadata (external API)
2. weekly_data - starters, valid_options, players, manager_data,
    transaction_ids, position replacement scores, ffWAR calculations
"""

import logging
import time
from typing import Literal

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.cache.updaters.player_ids_updater import (
    update_player_ids_cache,
)
from patriot_center_backend.cache.updaters.weekly_data_updater import (
    update_weekly_data_caches,
)
from patriot_center_backend.utils.sleeper_api import SLEEPER_CLIENT

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def update_all_caches(restart: Literal["partial", "full", None] = None) -> None:
    """Update all caches in dependency order."""
    start = time.perf_counter()

    if restart:
        CACHE_MANAGER.restart_all_caches(restart)

    SLEEPER_CLIENT.clear_cache()

    update_player_ids_cache()  # Step 1
    update_weekly_data_caches()  # Step 2

    elapsed = time.perf_counter() - start

    logger.info(
        f"Cache update completed in {int(elapsed // 60)}:{elapsed % 60:05.2f}"
    )
