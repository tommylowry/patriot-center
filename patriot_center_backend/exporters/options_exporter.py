"""Options exporters for Patriot Center."""

from patriot_center_backend.constants import NAME_TO_MANAGER_USERNAME
from patriot_center_backend.models import Player
from patriot_center_backend.utils.image_url_handler import get_image_url


def get_options_list() -> dict[str, dict[str, str | None]]:
    """Get list of options.

    Returns:
        List of options
    """
    data = {}

    players = Player.get_all_starters()
    for player in players:
        data[str(player)] = player.get_metadata()
        data[str(player)]["type"] = "player"

    for manager in NAME_TO_MANAGER_USERNAME:
        data[manager] = {
            "type": "manager",
            "name": manager,
            "full_name": manager,
            "image_url": get_image_url(manager),
        }

    return data
