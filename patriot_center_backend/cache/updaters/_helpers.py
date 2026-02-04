"""Helper functions for cache updaters."""

from typing import Any


def slugify(full_name: str) -> str:
    """Returns a slugified version of the player's full name.

    Args:
        full_name: The player's full name.

    Returns:
        A slugified version of the player's full name.
    """
    slug = full_name.lower()
    slug = slug.replace(" ", "%20")
    slug = slug.replace("'", "%27")
    return slug


def get_image_url(player_id: str) -> str:
    """Returns the URL of the player's image.

    If the player ID is numeric, returns the URL of the player's image.
    If the player ID is not numeric, returns the URL of the team logo.

    Args:
        player_id: The ID of the player.

    Returns:
        The URL of the player's image.
    """
    if player_id.isnumeric():
        return f"https://sleepercdn.com/content/nfl/players/{player_id}.jpg"
    else:
        return (
            f"https://sleepercdn.com/images/team_logos"
            f"/nfl/{player_id.lower()}.png"
        )


def get_full_name(player_info: dict[str, Any]) -> str:
    """Returns the player's full name.

    Args:
        player_info: The player's info.

    Returns:
        The player's full name.

    Raises:
        ValueError: If player_info does not contain 'first_name' and 'last_name'
            keys.
    """
    if "first_name" not in player_info or "last_name" not in player_info:
        raise ValueError(
            "player_info must contain 'first_name' and 'last_name' keys"
        )

    return (
        f"{player_info['first_name']} "
        f"{player_info['last_name']}"
    )
