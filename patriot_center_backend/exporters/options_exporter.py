"""Options exporters for Patriot Center."""

from patriot_center_backend.cache.queries.option_queries import (
    get_options_list_from_cache,
)


def get_options_list() -> dict[str, dict[str, str | None]]:
    """Public entry point for retrieving options list from cache.

    Returns:
        Nested dict shaped like players_cache subset.
    """
    return get_options_list_from_cache()
