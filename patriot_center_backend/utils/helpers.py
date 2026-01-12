from functools import lru_cache

from patriot_center_backend.cache import CACHE_MANAGER


@lru_cache(maxsize=1)
def _get_player_name_to_id():
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()
    return {
        player_info.get("full_name"): pid 
        for pid, player_info in player_ids_cache.items()
    }

def get_player_id(player_name: str) -> str:
    """
    Retrieve the player ID for a given player name from the player IDs cache.

    Args:
        player_name (str): The full name of the player.
        player_ids_cache (dict): A dictionary mapping player names to their IDs.

    Returns:
        str or None: The player ID if found, otherwise None.
    """
    return _get_player_name_to_id().get(player_name)

def get_player_name(player_id: str) -> str|None:
    """
    Retrieve the player name for a given player ID from the player IDs cache.

    Args:
        player_id (str): The ID of the player.
        player_ids_cache (dict): A dictionary mapping player names to their IDs.

    Returns:
        str or None: The player name if found, otherwise None.
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    player_info = player_ids_cache.get(player_id)
    if player_info:
        return player_info.get("full_name", None)
    return None