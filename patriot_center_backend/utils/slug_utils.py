from patriot_center_backend.cache import CACHE_MANAGER


def slugify(item: str) -> str:
    """
    Creates a URL-friendly slug by converting the input string to lowercase and
    replacing spaces and apostrophes with their URL-encoded equivalents.

    Example: "De'Von Achane" -> "de%27von%20achane"

    Args:
        item (str): The string to create a slug from.
    
    Returns:
        str: URL-friendly slug
    """
    slug = item.lower()
    slug = slug.replace(" ", "%20")
    slug = slug.replace("'", "%27")
    return slug

def slug_to_name(slug: str) -> str:
    """Convert a slug string to a player name.

    Args:
        slug (str): The slug string (e.g., "de%27von%20achane").

    Returns:
        str: The player name (e.g., "De'Von Achane").
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