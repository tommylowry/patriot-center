"""Batch updater for Patriot Center caches.

Responsibilities:
- Coordinate warming/updating of dependent caches with a single call.
- Delegates to per-cache loaders which are incremental/resumable.
- Optionally auto-commits cache changes to git (production mode).

Side effects:
- Disk I/O and network requests via delegated utilities.
- Git commits and pushes (if auto_commit_enabled).
"""
import os
from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache
from patriot_center_backend.utils.replacement_score_loader import load_or_update_replacement_score_cache
from patriot_center_backend.utils.ffWAR_loader import load_or_update_ffWAR_cache
from patriot_center_backend.utils.git_auto_commit import commit_and_push_cache_updates


def update_all_caches(auto_commit=None):
    """
    Update all caches (starters, replacement scores, ffWAR) in one call.

    Args:
        auto_commit (bool, optional): Whether to auto-commit cache changes to git.
            If None, reads from PATRIOT_AUTO_COMMIT_CACHE environment variable.
            Set to False for local development, True for production.

    Returns:
        dict: Snapshot of the three updated in-memory caches.
    """
    # Warm/update starters cache (incremental)
    starters_cache = load_or_update_starters_cache()
    # Warm/update replacement score cache (includes 3yr averages)
    replacement_score_cache = load_or_update_replacement_score_cache()
    # Warm/update ffWAR cache (simulation-based)
    ffWAR_cache = load_or_update_ffWAR_cache()

    # Auto-commit cache changes if enabled
    # Default to reading from environment variable
    if auto_commit is None:
        auto_commit = os.environ.get('PATRIOT_AUTO_COMMIT_CACHE', 'false').lower() == 'true'

    if auto_commit:
        print("\n🤖 Auto-commit enabled. Committing cache changes...")
        success = commit_and_push_cache_updates()
        if success:
            print("Cache changes committed and pushed to GitHub")
        else:
            print("Cache update succeeded but git commit failed")

    # Single consolidated return object for orchestration layers
    return {
        "starters_cache": starters_cache,
        "replacement_score_cache": replacement_score_cache,
        "ffWAR_cache": ffWAR_cache
    }

if __name__ == "__main__":
    # Direct invocation for manual cache updates
    # Auto-commit will be controlled by PATRIOT_AUTO_COMMIT_CACHE env var
    update_all_caches()