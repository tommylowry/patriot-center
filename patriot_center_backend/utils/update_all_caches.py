"""Batch updater for Patriot Center caches.

Responsibilities:
- Coordinate warming/updating of dependent caches with a single call.
- Delegates to per-cache loaders which are incremental/resumable.

Side effects:
- Disk I/O and network requests via delegated utilities.
"""
from patriot_center_backend.utils.starters_loader import update_starters_cache
from patriot_center_backend.utils.replacement_score_loader import update_replacement_score_cache
from patriot_center_backend.utils.player_data_loader import update_player_data_cache
from patriot_center_backend.utils.player_ids_loader import update_player_ids


def update_all_caches():
    """
    Update all caches (starters, replacement scores, ffWAR) in one call.

    Returns:
        dict: Snapshot of the three updated in-memory caches.
    """
    # update starters cache (incremental)
    starters_cache = update_starters_cache()
    # update replacement score cache (includes 3yr averages)
    replacement_score_cache = update_replacement_score_cache()
    # update player data cache (simulation-based)
    player_data_cache = update_player_data_cache()
    # update player ids cache
    player_ids_cache = update_player_ids()

    # Single consolidated return object for orchestration layers
    return {
        "starters_cache": starters_cache,
        "replacement_score_cache": replacement_score_cache,
        "player_data_cache": player_data_cache,
        "player_ids_cache": player_ids_cache,
    }

if __name__ == "__main__":
    # Direct invocation for manual cache updates
    update_all_caches()