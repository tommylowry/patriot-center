from patriot_center_backend.utils.cache_utils import load_cache
from patriot_center_backend.constants import PLAYERS_CACHE_FILE

def fetch_players():
    """
    Retrieve full player cache.

    Returns:
        dict: Cached player data.
    """
    return load_cache(PLAYERS_CACHE_FILE, players_cache=True)