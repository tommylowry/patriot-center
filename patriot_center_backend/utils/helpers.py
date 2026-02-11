"""Helper functions for the Patriot Center backend."""

from patriot_center_backend.cache import CACHE_MANAGER


def get_user_id(manager_name: str) -> str | None:
    """Retrieve the user ID for a given manager name from the manager cache.

    Args:
        manager_name: The name of the manager.

    Returns:
        The user ID if found, otherwise None.
    """
    manager_cache = CACHE_MANAGER.get_manager_metadata_cache()

    return manager_cache.get(manager_name, {}).get("summary", {}).get("user_id")
