"""Helper functions for the Patriot Center backend."""

from typing import Any

from patriot_center_backend.cache import CACHE_MANAGER


def get_user_id(manager_name: str) -> str | None:
    """Retrieve the user ID for a given manager name from the manager cache.

    Args:
        manager_name: The name of the manager.

    Returns:
        The user ID if found, otherwise None.
    """
    manager_cache = CACHE_MANAGER.get_manager_cache()

    return manager_cache.get(manager_name, {}).get("summary", {}).get("user_id")


def recursive_replace(data: Any, old_str: str, new_str: str) -> Any:
    """Recursively replaces all occurrences of `old_str` with `new_str`.

    Note:
    - This function recursively searches through dictionaries, lists, and
    strings to find and replace old_str with new_str.

    Args:
        data: The data structure to search and replace in.
        old_str: The string to search for and replace.
        new_str: The replacement string.

    Returns:
        Any: The modified data structure.
    """
    if isinstance(data, str):
        # Replace string in values/elements
        return data.replace(old_str, new_str)
    elif isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # Replace string in keys, then recurse on values
            new_key = k.replace(old_str, new_str)
            new_dict[new_key] = recursive_replace(v, old_str, new_str)
        return new_dict
    elif isinstance(data, list):
        # Recurse on list elements
        return [recursive_replace(item, old_str, new_str) for item in data]
    else:
        # Return other types (int, float, bool, etc.) as is
        return data
