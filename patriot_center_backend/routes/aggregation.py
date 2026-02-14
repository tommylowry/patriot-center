"""Aggregate player and manager statistics."""

from flask import Blueprint, Response, jsonify, request

from patriot_center_backend.exporters.aggregation_exporter import (
    get_aggregated_managers,
    get_aggregated_players,
    get_player_manager_aggregation,
)
from patriot_center_backend.models import Manager, Player
from patriot_center_backend.utils.argument_parser import parse_arguments
from patriot_center_backend.utils.data_formatters import to_records

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
        arg1: Year or week number or manager name.
        arg2: Year or week number or manager name.
        arg3: Year or week number or manager name.

    Returns:
        Response in JSON format and status code.
    """
    try:
        year, week, manager = parse_arguments(arg1, arg2, arg3)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    data = get_aggregated_players(manager, year, week)
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
    "/get_aggregated_managers/<string:player_id>",
    defaults={"arg2": None, "arg3": None},
    methods=["GET"],
)
@bp.route(
    "/get_aggregated_managers/<string:player_id>/<string:arg2>",
    defaults={"arg3": None},
    methods=["GET"],
)
@bp.route(
    "/get_aggregated_managers/<string:player_id>/<string:arg2>/<string:arg3>",
    methods=["GET"],
)
def get_aggregated_managers_route(
    player_id: str, arg2: str | None, arg3: str | None
) -> tuple[Response, int]:
    """Aggregate manager totals (points, games started, ffWAR) for a player.

    - Player name comes first as a required path component. Remaining args are
    interpreted as season and/or week. Underscores are converted to spaces to
    allow URL-friendly player names.
    - If `arg2` or `arg3` are not provided, result is for all seasons and weeks.

    Args:
        player_id: Player name key.
        arg2: Year or week number.
        arg3: Year or week number.

    Returns:
        Response in JSON format and status code.
    """
    try:
        year, week, _ = parse_arguments(arg2, arg3, None)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    data = get_aggregated_managers(Player(player_id), year, week)
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
    "/get_player_manager_aggregation/<string:player_id>/<string:manager>",
    defaults={"year": None, "week": None},
    methods=["GET"],
)
@bp.route(
    "/get_player_manager_aggregation/"
    "<string:player_id>/<string:manager>/<string:year>",
    defaults={"week": None},
    methods=["GET"],
)
@bp.route(
    "/get_player_manager_aggregation/"
    "<string:player_id>/<string:manager>/<string:year>/<string:week>",
    methods=["GET"],
)
def get_player_manager_aggregation_route(
    player_id: str,
    user_id: str,
    year: str | None,
    week: str | None,
) -> tuple[Response, int]:
    """Aggregate totals for a specific player-manager pairing.

    Player and manager are required path components. Remaining args are
    interpreted as season and/or week. Underscores are converted to spaces
    to allow URL-friendly player names.

    Args:
        player_id: The player_id to filter.
        user_id: The user_id to filter.
        year: Year or week number.
        week: Year or week number.

    Returns:
        Response in JSON format (aggregated stats or error) and status code.
    """
    manager = Manager(user_id)
    data = get_player_manager_aggregation(
        Player(player_id), manager, year=year, week=week,
    )
    if request.args.get("format") == "json":
        response = jsonify(data)

        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response, 200

    response = jsonify(
        to_records({manager.real_name: data}, key_name="manager")
    )


    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200
