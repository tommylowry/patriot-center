from patriot_center_backend.utils.player_ids_loader import load_player_ids

PLAYER_IDS_CACHE = load_player_ids()

def get_player_id(player_name):
    """
    Retrieve the player ID for a given player name from the player IDs cache.

    Args:
        player_name (str): The full name of the player.
        player_ids_cache (dict): A dictionary mapping player names to their IDs.

    Returns:
        str or None: The player ID if found, otherwise None.
    """
    for pid, player_info in PLAYER_IDS_CACHE.items():
        if player_info.get("full_name") == player_name:
            return pid
    return None

def get_player_name(player_id):
    """
    Retrieve the player name for a given player ID from the player IDs cache.

    Args:
        player_id (str): The ID of the player.
        player_ids_cache (dict): A dictionary mapping player names to their IDs.

    Returns:
        str or None: The player name if found, otherwise None.
    """
    player_info = PLAYER_IDS_CACHE.get(player_id)
    if player_info:
        return player_info.get("full_name", None)
    return None