"""Options exporters for Patriot Center."""

from patriot_center_backend.constants import NAME_TO_MANAGER_USERNAME
from patriot_center_backend.domains import Player
from patriot_center_backend.utils.image_url_handler import get_image_url


def get_options_list() -> dict[str, dict[str, str | None]]:
    """Get list of options.

    Returns:
        List of options
    """
    data = {}

    players = Player.get_all_starters()
    for player in players:
        data[str(player)] = {
            "full_name": player.full_name,
            "first_name": player.first_name,
            "last_name": player.last_name,
            "position": player.position,
            "team": player.team,
            "slug": player.slug,
            "player_id": player.player_id,
            "image_url": player.image_url,
            "type": "player",
        }

    for manager in NAME_TO_MANAGER_USERNAME:
        data[manager] = {
            "type": "manager",
            "name": manager,
            "full_name": manager,
            "slug": manager,
            "image_url": get_image_url(manager),
        }

    return data
