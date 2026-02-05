"""Aggregation utilities over starters data.

Exposes helpers to:
- Aggregate totals across weeks/seasons for a manager by player.
- Aggregate totals across weeks/seasons for a player by manager.

Key features:
- Fetches ffWAR scores for each player/week and includes them in aggregations
- Tracks playoff placements for players/managers
- Generates player image endpoints using Sleeper CDN
- Rounds financial totals to 2 decimals, ffWAR to 3 decimals

Notes:
- Results are simple dicts suitable for JSON responses.
- Totals are rounded to two decimals via Decimal normalization (ffWAR to 3).
"""

import logging
from decimal import Decimal
from typing import Any

from patriot_center_backend.cache.queries.aggregation_queries import (
    get_ffwar_from_cache,
    get_team,
)
from patriot_center_backend.cache.queries.starters_queries import (
    get_starters_from_cache,
)
from patriot_center_backend.domains.player import Player
from patriot_center_backend.utils.image_url_handler import get_image_url
from patriot_center_backend.utils.slug_utils import slugify

logger = logging.getLogger(__name__)


def get_aggregated_players(
    manager: str | None = None,
    season: int | None = None,
    week: int | None = None,
) -> dict[str, dict[str, Any]]:
    """Aggregate player metrics for a given manager.

    Traverses nested structure and collates:
    - total_points (rounded per update)
    - num_games_started
    - cumulative ffWAR (rounded per update)
    - position (taken from first occurrence)

    Args:
        manager: Target manager. Required for meaningful output.
        season: Optional season restriction.
        week: Optional week restriction.

    Returns:
        A dictionary containing player metrics for the given manager or all
        managers if no manager provided.
    """
    raw_dict = get_starters_from_cache(
        manager=manager, season=season, week=week
    )
    players_dict_to_return = {}

    if not raw_dict:
        return players_dict_to_return

    for year, weeks in raw_dict.items():
        for wk, managers in weeks.items():
            for mgr, manager_data in managers.items():
                for player_id, player_data in manager_data.items():
                    if player_id == "Total_Points":
                        # Skip aggregate row inside source structure
                        continue
                    player = Player(player_id)
                    player_data["ffWAR"] = player.get_ffwar(
                        year=year, week=wk, manager=mgr
                    )

                    if str(player) in players_dict_to_return:
                        _update_player_data(
                            players_dict_to_return,
                            player.full_name,
                            player_data,
                            mgr,
                            year,
                        )
                    else:
                        _initialize_player_data(
                            players_dict_to_return,
                            player.full_name,
                            player_data,
                            mgr,
                            year,
                        )

    return players_dict_to_return


def get_aggregated_managers(
    player_id: str,
    manager: str | None = None,
    year: str | None = None,
    week: str | None = None
) -> dict[str, dict[str, Any]]:
    """Aggregate manager metrics for appearances of a given player.

    Args:
        player_id: Player ID.
        manager: Optional manager restriction.
        year: Optional year restriction.
        week: Optional week restriction.

    Returns:
        A dictionary containing manager metrics for the given player.
    """
    player = Player(player_id)

    scoring_summary = player.get_scoring_summary(
        key="manager", year=year, week=week, manager=manager
    )

    for manager in scoring_summary:
        manager_summary = scoring_summary[manager]
        manager_summary["ffwar_per_game"] = round(
            manager_summary["ffwar"] / manager_summary["num_games"], 3
        )
        manager_summary["position"] = player.position
        manager_summary["player_image_endpoint"] = player.image_url
        manager_summary["slug"] = player.slug
        manager_summary["team"] = player.team

    return scoring_summary


def _update_player_data(
    players_dict: dict[str, dict[str, Any]],
    player: str,
    player_data: dict[str, Any],
    manager: str,
    year: str,
) -> None:
    """Update aggregated player data.

    Args:
        players_dict: Dictionary of aggregated player data.
        player: Player identifier.
        player_data: Dictionary of player data.
        manager: Manager identifier.
        year: Season year.

    Updates the aggregated player data by adding the player data.
    Rounds total_points, ffWAR, and ffWAR_per_game to appropriate precision
    using Decimal. Tracks playoff placements for players/managers.
    """
    player_dict_item = players_dict[player]

    # Accumulate totals
    player_dict_item["total_points"] += player_data["points"]
    player_dict_item["ffWAR"] += player_data["ffWAR"]
    player_dict_item["num_games_started"] += 1
    player_dict_item["ffWAR_per_game"] = (
        player_dict_item["ffWAR"] / player_dict_item["num_games_started"]
    )

    # Round to appropriate precision using Decimal for exact rounding
    player_dict_item["total_points"] = float(
        Decimal(player_dict_item["total_points"])
        .quantize(Decimal("0.01"))
        .normalize()
    )
    player_dict_item["ffWAR"] = float(
        Decimal(player_dict_item["ffWAR"])
        .quantize(Decimal("0.001"))
        .normalize()
    )
    player_dict_item["ffWAR_per_game"] = float(
        Decimal(player_dict_item["ffWAR_per_game"])
        .quantize(Decimal("0.001"))
        .normalize()
    )
    players_dict[player] = player_dict_item

    # Track playoff finishes (1st, 2nd, 3rd place) by manager and year
    if "placement" in player_data:
        players_dict = _handle_playoff_placement(
            players_dict, player, manager, year, player_data["placement"]
        )

    return


def _initialize_player_data(
    players_dict: dict[str, dict[str, Any]],
    player: str,
    player_data: dict[str, Any],
    manager: str,
    year: str,
) -> None:
    """Initialize aggregated player data.

    Args:
        players_dict: Dictionary of aggregated player data.
        player: Player identifier.
        player_data: Dictionary of player data.
        manager: Manager identifier.
        year: Season year.

    Initializes the aggregated player data by creating a new entry.
    Rounds total_points, ffWAR, and ffWAR_per_game to appropriate precision
    using Decimal. Tracks playoff placements for players/managers.
    """
    players_dict[player] = {
        "total_points": player_data["points"],
        "num_games_started": 1,
        "ffWAR": player_data["ffWAR"],
        "ffWAR_per_game": player_data["ffWAR"],
        "position": player_data["position"],
        "player_image_endpoint": get_image_url(player),
        "slug": slugify(player),
        "team": get_team(player),
    }

    # Track playoff finishes if this is the last playoff week
    if "placement" in player_data:
        players_dict = _handle_playoff_placement(
            players_dict, player, manager, year, player_data["placement"]
        )

    return


def _handle_playoff_placement(
    aggregation_dict: dict[str, dict[str, Any]],
    primary_item: str,
    secondary_item: str,
    year: str,
    placement: int,
) -> dict[str, dict[str, Any]]:
    """Handles updating the playoff placement for a manager/player pair.

    Args:
        aggregation_dict: Dictionary of aggregated data.
        primary_item: Primary item identifier (e.g., manager name).
        secondary_item: Secondary item identifier (e.g., player name).
        year: Season year as string.
        placement: Placement integer (1st, 2nd, 3rd).

    Returns:
        Updated aggregation dictionary.
    """
    playoff_placement = aggregation_dict[primary_item].get(
        "playoff_placement", {}
    )
    if not playoff_placement:
        aggregation_dict[primary_item]["playoff_placement"] = {
            secondary_item: {year: placement}
        }
    elif not playoff_placement.get(secondary_item):
        playoff_placement[secondary_item] = {year: placement}
    elif not playoff_placement[secondary_item].get(year):
        playoff_placement[secondary_item][year] = placement

    return aggregation_dict
