from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache
from patriot_center_backend.utils.replacement_score_loader import load_or_update_replacement_score_cache


def update_all_caches():
    """
    Update all caches (starters and replacement scores).
    """
    starters_cache = load_or_update_starters_cache()
    replacement_score_cache = load_or_update_replacement_score_cache()
    return {
        "starters_cache": starters_cache,
        "replacement_score_cache": replacement_score_cache,
    }