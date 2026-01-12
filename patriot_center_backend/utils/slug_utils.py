"""
This module provides utility functions for creating and converting slugs.
"""

from patriot_center_backend.cache import CACHE_MANAGER


def slugify(item: str) -> str:
    """
    Creates a URL-friendly slug by converting the input string to lowercase and
    replacing spaces and apostrophes with their URL-encoded equivalents.

    Args:
        item (str): The input string.

    Returns:
        str: The URL-friendly slug.
    """
    slug = item.lower()
    slug = slug.replace(" ", "%20")
    slug = slug.replace("'", "%27")
    return slug

def slug_to_name(slug: str) -> str:
    """
    Convert a slug string to a player name.

    Args:
        slug (str): The slug string.

    Returns:
        str: The player name.
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