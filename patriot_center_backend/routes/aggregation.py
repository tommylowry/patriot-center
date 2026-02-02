"""Aggregate player and manager statistics."""

from flask import Blueprint, Response, jsonify, request

from patriot_center_backend.exporters.aggregation_exporter import (
    get_aggregated_managers,
    get_aggregated_players,
    get_player_manager_aggregation,
)
from patriot_center_backend.utils.argument_parser import parse_arguments
from patriot_center_backend.utils.data_formatters import to_records
from patriot_center_backend.utils.slug_utils import slug_to_name

bp = Blueprint("aggregation", __name__)


@bp.route(
    "/get_aggregated_players",
    defaults={"arg1": None, "arg2": None, "arg3": None},
    methods=["GET"],
)
@bp.route(
    "/get_aggregated_players/<string:arg1>",
    defaults={"arg2": None, "arg3": None},
    methods=["GET"],
)
@bp.route(
    "/get_aggregated_players/<string:arg1>/<string:arg2>",
    defaults={"arg3": None},
    methods=["GET"],
)
@bp.route(
    "/get_aggregated_players/<string:arg1>/<string:arg2>/<string:arg3>",
    methods=["GET"],
)
def get_aggregated_players_route(
    arg1: str | None, arg2: str | None, arg3: str | None
) -> tuple[Response, int]:
    """Aggregate player totals (points, games started, ffWAR) for a manager.

    Uses same positional inference rules as get_starters. Returns either raw
    aggregation or flattened record list.

    Args:
        arg1 (str | None): Season (year) or week number or manager name.
        arg2 (str | None): Season (year) or week number or manager name.
        arg3 (str | None): Season (year) or week number or manager name.

    Returns:
        Response in JSON format and status code.
    """
    try:
        year, week, manager = parse_arguments(arg1, arg2, arg3)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    data = get_aggregated_players(manager=manager, season=year, week=week)
    if request.args.get("format") == "json":
        response = jsonify(data)

        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response, 200

    response = jsonify(to_records(data))

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@bp.route(
    "/get_aggregated_managers/<string:player>",
    defaults={"arg2": None, "arg3": None},
    methods=["GET"],
)
@bp.route(
    "/get_aggregated_managers/<string:player>/<string:arg2>",
    defaults={"arg3": None},
    methods=["GET"],
)
@bp.route(
    "/get_aggregated_managers/<string:player>/<string:arg2>/<string:arg3>",
    methods=["GET"],
)
def get_aggregated_managers_route(
    player: str, arg2: str | None, arg3: str | None
) -> tuple[Response, int]:
    """Aggregate manager totals (points, games started, ffWAR) for a player.

    - Player name comes first as a required path component. Remaining args are
    interpreted as season and/or week. Underscores are converted to spaces to
    allow URL-friendly player names.
    - If `arg2` or `arg3` are not provided, result is for all seasons and weeks.

    Args:
        player: The player to filter.
        arg2: Season (year) or week number.
        arg3: Season (year) or week number.

    Returns:
        Response in JSON format and status code.
    """
    player = slug_to_name(player)  # Convert slug to player name

    try:
        year, week, _ = parse_arguments(arg2, arg3, None)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    data = get_aggregated_managers(player=player, season=year, week=week)
    if request.args.get("format") == "json":
        response = jsonify(data)

        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response, 200

    response = jsonify(to_records(data, key_name="manager"))

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@bp.route(
    "/get_player_manager_aggregation/<string:player>/<string:manager>",
    defaults={"year": None, "week": None},
    methods=["GET"],
)
@bp.route(
    "/get_player_manager_aggregation/"
    "<string:player>/<string:manager>/<string:year>",
    defaults={"week": None},
    methods=["GET"],
)
@bp.route(
    "/get_player_manager_aggregation/"
    "<string:player>/<string:manager>/<string:year>/<string:week>",
    methods=["GET"],
)
def get_player_manager_aggregation_route(
    player: str,
    manager: str,
    year: str | None,
    week: str | None,
) -> tuple[Response, int]:
    """Aggregate totals for a specific player-manager pairing.

    Player and manager are required path components. Remaining args are
    interpreted as season and/or week. Underscores are converted to spaces
    to allow URL-friendly player names.

    Args:
        player: The player to filter.
        manager: The manager to filter.
        year: Season (year) or week number.
        week: Season (year) or week number.

    Returns:
        Response in JSON format (aggregated stats or error) and status code.
    """
    player = slug_to_name(player)  # Convert slug to player name

    data = get_player_manager_aggregation(
        player, manager, season=year, week=week
    )
    if request.args.get("format") == "json":
        response = jsonify(data)

        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response, 200

    response = jsonify(to_records(data, key_name="manager"))

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200
