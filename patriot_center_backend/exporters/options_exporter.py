"""Options exporters for Patriot Center."""

from patriot_center_backend.models import Manager, Player


def get_options_list() -> dict[str, dict[str, str | None]]:
    """Get list of options.

    Returns:
        List of options
    """
    data = {}

    players = Player.get_players()
    for player in players:
        data[str(player)] = player.get_metadata()

    for manager in Manager.get_managers():
        data[str(manager)] = manager.get_metadata()

    return data
