"""Helper functions for the Patriot Center backend."""

from functools import lru_cache

from patriot_center_backend.cache import CACHE_MANAGER


@lru_cache(maxsize=1)
def _get_player_name_to_id() -> dict[str, str]:
    """Return a dictionary mapping full player names to their IDs.

    This function is an LRU cache with a size of 1, meaning it will only store
        the most recent call's result.
    This is useful for speeding up repeated calls to this function.

    Returns:
        dict[str, str]: A dictionary mapping full player names to their IDs.
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    return {
        player_info["full_name"]: pid
        for pid, player_info in player_ids_cache.items()
    }


def get_player_id(player_name: str) -> str | None:
    """Retrieve the player ID for a given player name from the player IDs cache.

    Args:
        player_name: The full name of the player.

    Returns:
        The player ID if found, otherwise None.
    """
    return _get_player_name_to_id().get(player_name)


def get_player_name(player_id: str) -> str | None:
    """Retrieve the player name for a given player ID from the player IDs cache.

    Args:
        player_id: The ID of the player.

    Returns:
        The player name if found, otherwise None.
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    return player_ids_cache.get(player_id, {}).get("full_name")

def get_player_position(player_id: str) -> str | None:
    """Retrieve the player position for a given player ID from the IDs cache.

    Args:
        player_id: The ID of the player.

    Returns:
        The player position if found, otherwise None.
    """
    player_ids_cache = CACHE_MANAGER.get_player_ids_cache()

    return player_ids_cache.get(player_id, {}).get("position")

def get_user_id(manager_name: str) -> str | None:
    """Retrieve the user ID for a given manager name from the manager cache.

    Args:
        manager_name: The name of the manager.

    Returns:
        The user ID if found, otherwise None.
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    return manager_cache.get(manager_name, {}).get("summary", {}).get("user_id")
