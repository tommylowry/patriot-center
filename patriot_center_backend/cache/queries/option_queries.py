"""Option queries."""

from copy import deepcopy

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import NAME_TO_MANAGER_USERNAME


def get_options_list_from_cache() -> dict[str, dict[str, str | None]]:
    """Public entry point for retrieving options list from cache.

    Returns:
        Nested dict shaped like players_cache subset.
    """
    players_cache = CACHE_MANAGER.get_players_cache()

    data = deepcopy(players_cache)

    for manager in NAME_TO_MANAGER_USERNAME:
        data[manager] = {
            "type": "manager",
            "name": manager,
            "full_name": manager,
            "slug": manager,
        }

    return data
