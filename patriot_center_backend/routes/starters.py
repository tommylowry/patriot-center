"""Fetch starters filtered by optional season (year), manager, and week."""

from flask import Blueprint, Response, jsonify, request

from patriot_center_backend.exporters.starters_exporter import get_starters
from patriot_center_backend.utils.argument_parser import parse_arguments
from patriot_center_backend.utils.data_formatters import to_records

bp = Blueprint("starters", __name__)


# Multiple route variants allow optional path parameters (year, manager, week)
@bp.route(
    "/get_starters",
    defaults={"arg1": None, "arg2": None, "arg3": None},
    methods=["GET"],
)
@bp.route(
    "/get_starters/<string:arg1>",
    defaults={"arg2": None, "arg3": None},
    methods=["GET"],
)
@bp.route(
    "/get_starters/<string:arg1>/<string:arg2>",
    defaults={"arg3": None},
    methods=["GET"],
)
@bp.route(
    "/get_starters/<string:arg1>/<string:arg2>/<string:arg3>", methods=["GET"]
)
def get_starters_route(
    arg1: str | None, arg2: str | None, arg3: str | None
) -> tuple[Response, int]:
    """Fetch starters filtered by optional season (year), manager, and week.

    Path arguments are positional and inferred by type/value:
    - League IDs -> season
    - Week numbers 1-17 -> week
    - Known manager names -> manager

    Args:
        arg1: Season (year) or week number or manager name.
        arg2: Season (year) or week number or manager name.
        arg3: Season (year) or week number or manager name.

    Returns:
        Response in JSON format and status code.
            - If format=json, returns nested JSON.
            - Otherwise, returns flattened records.
    """
    # Parse positional arguments to determine filter values
    year, week, manager = parse_arguments(arg1, arg2, arg3)

    # Fetch filtered starters data from cache
    data = get_starters(season=year, manager=manager, week=week)

    # Return either nested JSON or flattened records based on format parameter
    if request.args.get("format") == "json":
        response = jsonify(data)

        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response, 200

    response = jsonify(to_records(data))

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200
