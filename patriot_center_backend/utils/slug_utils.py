"""This module provides utility functions for creating and converting slugs."""

from patriot_center_backend.cache import CACHE_MANAGER


def slugify(item: str) -> str:
    """Creates a URL-friendly slug.

    This function creates a slug by converting the input string to lowercase and
    replacing spaces and apostrophes with their URL-encoded equivalents.

    Args:
        item: The input string.

    Returns:
        The URL-friendly slug.
    """
    slug = item.lower()
    slug = slug.replace(" ", "%20")
    slug = slug.replace("'", "%27")
    return slug


def slug_to_name(slug: str) -> str:
    """Convert a slug string to a player name.

    - This function takes a slug string as input and returns the corresponding
    player name.
    - If no match is found, the original slug string is returned.

    Args:
        slug: The slug string.

    Returns:
        The player full name.
    """
    if not slug:
        return slug

    players_cache = CACHE_MANAGER.get_players_cache()

    # ensure consistent encoding for lookup
    slug = slugify(slug)
    for p in players_cache:
        if players_cache[p]["slug"] == slug:
            return p

    return slug  # Fallback to returning the original string if no match found
