"""Exporters for aggregating data."""

from typing import Any

from patriot_center_backend.models import Manager, Player


def get_player_manager_aggregation(
    player: Player,
    manager: Manager,
    year: str | None,
    week: str | None,
) -> dict[str, Any]:
    """Aggregate totals for a specific player-manager pairing.

    Args:
        player: The player to filter.
        manager: The manager to filter.
        year: Optional year restriction.
        week: Optional week restriction.

    Returns:
        A dictionary containing player metrics for the given manager.
    """
    scoring_summary = player.get_scoring_summary(
        year=year, week=week, manager=manager
    )

    _populate_scoring_summary(scoring_summary, player)

    return scoring_summary


def get_aggregated_players(
    manager: Manager | None,
    year: str | None,
    week: str | None,
) -> dict[str, dict[str, Any]]:
    """Aggregate player metrics for a given manager, year, and/or week.

    Args:
        manager: Optional manager restriction.
        year: Optional year restriction.
        week: Optional week restriction.

    Returns:
        A dictionary containing player metrics for the given manager.
    """
    players_dict_to_return = {}

    players = Player.get_all_starters(year, week, manager)

    for player in players:
        scoring_summary = player.get_scoring_summary(
            year=year, week=week, manager=manager
        )

        _populate_scoring_summary(scoring_summary, player)

        players_dict_to_return[str(player)] = scoring_summary

    return players_dict_to_return


def get_aggregated_managers(
    player: Player,
    year: str | None,
    week: str | None,
) -> dict[str, dict[str, Any]]:
    """Aggregate manager metrics for appearances of a given player.

    Args:
        player: The player to filter.
        year: Optional year restriction.
        week: Optional week restriction.

    Returns:
        A dictionary containing manager metrics for the given player.
    """
    scoring_summary = player.get_grouped_scoring_summary(
        group_by="manager", year=year, week=week
    )

    for manager in list(scoring_summary.keys()):
        manager_summary = scoring_summary[manager]

        _populate_scoring_summary(manager_summary, player)

    return scoring_summary


def _populate_scoring_summary(
    scoring_summary: dict[str, Any], player: Player
) -> None:
    """Populate scoring summary with player data.

    Args:
        scoring_summary: The scoring summary dictionary.
        player: The player object.
    """
    scoring_summary["player"] = player.full_name
    scoring_summary["position"] = player.position
    scoring_summary["player_image_endpoint"] = player.image_url
    scoring_summary["team"] = player.team
