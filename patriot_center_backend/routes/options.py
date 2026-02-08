"""Options endpoints for Patriot Center."""

from flask import Blueprint, Response, jsonify, request

from patriot_center_backend.exporters.dynamic_filter_exporter import (
    get_dynamic_filter_options,
)
from patriot_center_backend.exporters.options_exporter import (
    get_options_list,
)
from patriot_center_backend.models import Player
from patriot_center_backend.utils.data_formatters import to_records

bp = Blueprint("options", __name__)


@bp.route("/options/list", methods=["GET"])
def get_options_list_route() -> tuple[Response, int]:
    """Endpoint to list all players and managers in the cache.

    Returns:
        Response in JSON format and status code.
    """
    data = get_options_list()

    if request.args.get("format") == "json":
        response = jsonify(data)

        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response, 200

    response = jsonify(to_records(data, key_name="name"))

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@bp.route("/dynamic_filtering", methods=["GET"])
def get_dynamic_filter_options_route() -> tuple[Response, int]:
    """Endpoint retreive filtered data for provided input combinations.

    Receive any combination of season, week, manager, player, and position
    and dynamically filter the possible valid inputs based on the inputs
    provided.

    Acceptable arguments:
    - yr: Season (year)
    - wk: Week number
    - mgr: Manager name
    - pos: Player position
    - plyr: Player ID

    Returns:
        Response in JSON format and status code.
    """
    acceptable_args = ["yr", "wk", "mgr", "pos", "plyr"]
    for arg in request.args:
        if arg not in acceptable_args:
            return jsonify({"error": f"Invalid argument: {arg}"}), 400

    yr = request.args.get("yr")
    wk = request.args.get("wk")
    mgr = request.args.get("mgr")
    pos = request.args.get("pos")
    plyr = request.args.get("plyr")

    player = Player(plyr) if plyr else None

    try:
        data = get_dynamic_filter_options(yr, wk, mgr, pos, player)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    response = jsonify(data)

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200
