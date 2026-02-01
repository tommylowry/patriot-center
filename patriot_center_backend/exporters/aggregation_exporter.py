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
from patriot_center_backend.utils.image_url_handler import get_image_url
from patriot_center_backend.utils.slug_utils import slugify

logger = logging.getLogger(__name__)


def get_player_manager_aggregation(
    player: str,
    manager: str,
    season: str | None = None,
    week: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Aggregate metrics for a specific player-manager pairing.

    Args:
        player: Player name key.
        manager: Manager username key.
        season: Optional season restriction.
        week: Optional week restriction.

    Returns:
        A dictionary containing the player-manager aggregation.
    """
    season_int = None
    week_int = None
    if season and season.isnumeric():
        season_int = int(season)
    if week and week.isnumeric():
        week_int = int(week)
    player_data = get_aggregated_managers(
        player, season=season_int, week=week_int
    )
    if manager not in player_data:
        return {}

    return {manager: player_data[manager]}


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
                for player, player_data in manager_data.items():
                    if player == "Total_Points":
                        # Skip aggregate row inside source structure
                        continue
                    ffwar_score = get_ffwar_from_cache(
                        player, season=year, week=wk
                    )
                    player_data["ffWAR"] = ffwar_score

                    if player in players_dict_to_return:
                        _update_player_data(
                            players_dict_to_return,
                            player,
                            player_data,
                            mgr,
                            year,
                        )
                    else:
                        _initialize_player_data(
                            players_dict_to_return,
                            player,
                            player_data,
                            mgr,
                            year,
                        )

    return players_dict_to_return


def get_aggregated_managers(
    player: str, season: int | None = None, week: int | None = None
) -> dict[str, dict[str, Any]]:
    """Aggregate manager metrics for appearances of a given player.

    Args:
        player: Player name key.
        season: Optional season restriction.
        week: Optional week restriction.

    Returns:
        A dictionary containing manager metrics for the given player.
    """
    raw_dict = get_starters_from_cache(season=season, week=week)
    managers_dict_to_return = {}

    if not raw_dict:
        return managers_dict_to_return

    for year, weeks in raw_dict.items():
        for wk, managers in weeks.items():
            for manager, manager_data in managers.items():
                if player in manager_data:
                    raw_item = manager_data[player]
                    ffwar_score = get_ffwar_from_cache(
                        player, season=year, week=wk
                    )
                    raw_item["ffWAR"] = ffwar_score

                    if manager in managers_dict_to_return:
                        _update_manager_data(
                            managers_dict_to_return,
                            manager,
                            raw_item,
                            player,
                            year,
                        )
                    else:
                        _initialize_manager_data(
                            managers_dict_to_return,
                            manager,
                            raw_item,
                            player,
                            year,
                        )

    return managers_dict_to_return


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


def _update_manager_data(
    managers_dict: dict[str, dict[str, Any]],
    manager: str,
    raw_item: dict[str, Any],
    player: str,
    year: str,
) -> None:
    """Update aggregated manager data.

    Args:
        managers_dict: Dictionary of aggregated manager data.
        manager: Manager identifier.
        raw_item: Dictionary of raw manager data.
        player: Player identifier.
        year: Season year.

    Updates the aggregated manager data by adding the raw manager data.
    Rounds total_points, ffWAR, and ffWAR_per_game to appropriate precision
    using Decimal. Tracks playoff placements for managers/players.
    """
    manager_dict_item = managers_dict[manager]
    manager_dict_item["total_points"] += raw_item["points"]
    manager_dict_item["ffWAR"] += raw_item["ffWAR"]
    manager_dict_item["num_games_started"] += 1

    manager_dict_item["ffWAR_per_game"] = (
        manager_dict_item["ffWAR"] / manager_dict_item["num_games_started"]
    )

    manager_dict_item["total_points"] = float(
        Decimal(manager_dict_item["total_points"])
        .quantize(Decimal("0.01"))
        .normalize()
    )
    manager_dict_item["ffWAR"] = float(
        Decimal(manager_dict_item["ffWAR"])
        .quantize(Decimal("0.001"))
        .normalize()
    )
    manager_dict_item["ffWAR_per_game"] = float(
        Decimal(manager_dict_item["ffWAR_per_game"])
        .quantize(Decimal("0.001"))
        .normalize()
    )

    managers_dict[manager] = manager_dict_item

    # Handle playoff placement if present
    if "placement" in raw_item:
        managers_dict = _handle_playoff_placement(
            managers_dict, manager, player, year, raw_item["placement"]
        )

    return


def _initialize_manager_data(
    managers_dict: dict[str, dict[str, Any]],
    manager: str,
    raw_item: dict[str, Any],
    player: str,
    year: str,
) -> None:
    """Initialize aggregated manager data for a given player.

    Args:
        managers_dict: Dictionary of aggregated manager data.
        manager: Manager identifier.
        raw_item: Dictionary of raw data for a player.
        player: Player identifier.
        year: Season year.

    Initializes the aggregated manager data by creating a new entry.
    Rounds total_points, ffWAR, and ffWAR_per_game to appropriate precision
    using Decimal. Tracks playoff placements for players/managers.
    """
    managers_dict[manager] = {
        "player": player,  # Include the player name
        "total_points": raw_item["points"],
        "num_games_started": 1,
        "ffWAR": raw_item["ffWAR"],
        "ffWAR_per_game": raw_item["ffWAR"],
        "position": raw_item["position"],
        "player_image_endpoint": get_image_url(player),
        "slug": slugify(player),
        "team": get_team(player),
    }

    # Handle playoff placement if present
    if "placement" in raw_item:
        managers_dict = _handle_playoff_placement(
            managers_dict, manager, player, year, raw_item["placement"]
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
