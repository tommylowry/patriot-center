"""Flask application for the Patriot Center backend API.

This module defines the REST API endpoints for the Patriot Center fantasy
football analytics platform. It provides endpoints for:
- Fetching starter data filtered by season, week, and manager
- Aggregating player and manager statistics
- Listing available players and valid filter options
- Health and liveness checks

All endpoints support flexible positional arguments that are automatically
parsed to determine whether they represent years, weeks, managers, or players.

The API supports two response formats:
- Default: Flattened record list suitable for tabular display
- format=json: Nested hierarchical structure preserving original cache shape
"""

from copy import deepcopy
from typing import Any, Literal

from flask import Flask, Response, jsonify, request
from flask_cors import CORS

from patriot_center_backend.cache import CACHE_MANAGER
from patriot_center_backend.constants import (
    LEAGUE_IDS,
    NAME_TO_MANAGER_USERNAME,
)
from patriot_center_backend.dynamic_filtering import dynamic_filter
from patriot_center_backend.managers.data_exporter import (
    get_head_to_head,
    get_manager_awards,
    get_manager_summary,
    get_manager_transactions,
    get_managers_list,
)
from patriot_center_backend.services.aggregated_data import (
    fetch_aggregated_managers,
    fetch_player_manager_aggregation,
)
from patriot_center_backend.utils.slug_utils import slug_to_name

app = Flask(__name__)

# Configure CORS for production (Netlify frontend)
CORS(
    app,
    resources={
        r"/get_aggregated_players*": {
            "origins": ["https://patriotcenter.netlify.app"]
        },
        r"/get_starters*": {"origins": ["https://patriotcenter.netlify.app"]},
        r"/get_aggregated_managers*": {
            "origins": ["https://patriotcenter.netlify.app"]
        },
        r"/options/list": {"origins": ["https://patriotcenter.netlify.app"]},
        r"/dynamic_filtering*": {
            "origins": ["https://patriotcenter.netlify.app"]
        },
        r"/get_player_manager_aggregation*": {
            "origins": ["https://patriotcenter.netlify.app"]
        },
        r"/get/managers/list": {
            "origins": ["https://patriotcenter.netlify.app"]
        },
        r"/api/managers/*": {"origins": ["https://patriotcenter.netlify.app"]},
    },
)
CORS(app)  # Enable CORS for all routes during development


@app.route("/")
def index() -> tuple[Response, int]:
    """Root endpoint with basic info.

    Returns:
        Response in JSON format with service name, version, and available
            endpoints.
    """
    return jsonify(
        {
            "service": "Patriot Center Backend",
            "version": "1.0.0",
            "endpoints": [
                "/get_starters",
                "/get_aggregated_players",
                "/get_aggregated_managers/<player>",
                "/dynamic_filtering",
                "/options/list",
                "/get/managers/list/<active_only>",
                "/api/managers/<manager_name>/summary",
                "/api/managers/<manager_name>/head-to-head/<opponent_name>",
                "/api/managers/<manager_name>/transactions",
                "/api/managers/<manager_name>/awards",
                "/ping",
                "/health",
            ],
        }
    ), 200


@app.route("/ping")
def ping() -> tuple[str, int]:
    """Liveness check endpoint.

    Returns:
        "pong" and 200
    """
    return "pong", 200


@app.route("/health")
def health() -> tuple[Response, int]:
    """Health check endpoint.

    Returns:
        Response in JSON format with "status": "healthy" and 200
    """
    return jsonify({"status": "healthy"}), 200


# Multiple route variants allow optional path parameters (year, manager, week)
@app.route(
    "/get_starters",
    defaults={"arg1": None, "arg2": None, "arg3": None},
    methods=["GET"],
)
@app.route(
    "/get_starters/<string:arg1>",
    defaults={"arg2": None, "arg3": None},
    methods=["GET"],
)
@app.route(
    "/get_starters/<string:arg1>/<string:arg2>",
    defaults={"arg3": None},
    methods=["GET"],
)
@app.route(
    "/get_starters/<string:arg1>/<string:arg2>/<string:arg3>", methods=["GET"]
)
def get_starters(
    arg1: str | None, arg2: str | None, arg3: str | None
) -> tuple[Response, int]:
    """Fetch starters filtered by optional season (year), manager, and week.

    Path arguments are positional and inferred by type/value:
    - League IDs -> season
    - Week numbers 1-17 -> week
    - Known manager names -> manager

    Args:
        arg1 (str | None): Season (year) or week number or manager name.
        arg2 (str | None): Season (year) or week number or manager name.
        arg3 (str | None): Season (year) or week number or manager name.

    Returns:
        Response in JSON format and status code.
            - If format=json, returns nested JSON.
            - Otherwise, returns flattened records.
    """
    from patriot_center_backend.services.managers import fetch_starters

    # Parse positional arguments to determine filter values
    year, week, manager = parse_arguments(arg1, arg2, arg3)

    # Fetch filtered starters data from cache
    data = fetch_starters(season=year, manager=manager, week=week)

    # Return either nested JSON or flattened records based on format parameter
    if request.args.get("format") == "json":
        response = jsonify(data)

        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response, 200

    response = jsonify(_to_records(data))

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@app.route(
    "/get_aggregated_players",
    defaults={"arg1": None, "arg2": None, "arg3": None},
    methods=["GET"],
)
@app.route(
    "/get_aggregated_players/<string:arg1>",
    defaults={"arg2": None, "arg3": None},
    methods=["GET"],
)
@app.route(
    "/get_aggregated_players/<string:arg1>/<string:arg2>",
    defaults={"arg3": None},
    methods=["GET"],
)
@app.route(
    "/get_aggregated_players/<string:arg1>/<string:arg2>/<string:arg3>",
    methods=["GET"],
)
def get_aggregated_players(
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
    from patriot_center_backend.services.aggregated_data import (
        fetch_aggregated_players,
    )

    try:
        year, week, manager = parse_arguments(arg1, arg2, arg3)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    data = fetch_aggregated_players(manager=manager, season=year, week=week)
    if request.args.get("format") == "json":
        response = jsonify(data)

        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response, 200

    response = jsonify(_to_records(data))

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@app.route(
    "/get_aggregated_managers/<string:player>",
    defaults={"arg2": None, "arg3": None},
    methods=["GET"],
)
@app.route(
    "/get_aggregated_managers/<string:player>/<string:arg2>",
    defaults={"arg3": None},
    methods=["GET"],
)
@app.route(
    "/get_aggregated_managers/<string:player>/<string:arg2>/<string:arg3>",
    methods=["GET"],
)
def get_aggregated_managers(
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

    data = fetch_aggregated_managers(player=player, season=year, week=week)
    if request.args.get("format") == "json":
        response = jsonify(data)

        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response, 200

    response = jsonify(_to_records(data, key_name="manager"))

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@app.route(
    "/get_player_manager_aggregation/<string:player>/<string:manager>",
    defaults={"year": None, "week": None},
    methods=["GET"],
)
@app.route(
    "/get_player_manager_aggregation/"
    "<string:player>/<string:manager>/<string:year>",
    defaults={"week": None},
    methods=["GET"],
)
@app.route(
    "/get_player_manager_aggregation/"
    "<string:player>/<string:manager>/<string:year>/<string:week>",
    methods=["GET"],
)
def get_player_manager_aggregation(
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

    data = fetch_player_manager_aggregation(
        player, manager, season=year, week=week
    )
    if request.args.get("format") == "json":
        response = jsonify(data)

        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response, 200

    response = jsonify(_to_records(data, key_name="manager"))

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@app.route("/options/list", methods=["GET"])
def list_players() -> tuple[Response, int]:
    """Endpoint to list all players and managers in the cache.

    Returns:
        Response in JSON format and status code.
    """
    players_cache = CACHE_MANAGER.get_players_cache()

    data = deepcopy(players_cache)

    for manager in NAME_TO_MANAGER_USERNAME:
        data[manager] = {
            "type": "manager",
            "name": manager,
            "full_name": manager,
            "slug": manager,
        }

    if request.args.get("format") == "json":
        response = jsonify(data)

        # Cache for 1 hour
        response.headers["Cache-Control"] = "public, max-age=3600"
        return response, 200

    response = jsonify(_to_records(data, key_name="name"))

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@app.route("/dynamic_filtering", methods=["GET"])
def dynamic_filtering() -> tuple[Response, int]:
    """Endpoint retreive filtered data for provided input combinations.

    Receive any combination of season, week, manager, player, and position
    and dynamically filter the possible valid inputs based on the inputs
    provided.

    Acceptable arguments:
    - yr: Season (year)
    - wk: Week number
    - mgr: Manager name
    - pos: Player position
    - plyr: Player name

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

    if plyr:
        plyr = slug_to_name(plyr)

    try:
        data = dynamic_filter.filter(
            year=yr, week=wk, manager=mgr, position=pos, player=plyr
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    response = jsonify(data)

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@app.route("/get/managers/list/<string:active_only>", methods=["GET"])
def list_managers(
    active_only: Literal["true", "false"],
) -> tuple[Response, int]:
    """Endpoint to list all managers in the system and their top-level info.

    Args:
        active_only: Whether to return only active managers

    Returns:
        Response in JSON format and status code.
    """
    if active_only == "true":
        bool_active_only = True
    elif active_only == "false":
        bool_active_only = False
    else:
        return jsonify(
            {"error": f"{active_only} is not acceptable, only true/false."}
        ), 400

    try:
        data = get_managers_list(bool_active_only)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    response = jsonify(data)

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@app.route(
    "/api/managers/<string:manager_name>/summary",
    defaults={"year": None},
    methods=["GET"],
)
@app.route(
    "/api/managers/<string:manager_name>/summary/<string:year>", methods=["GET"]
)
def manager_summary(
    manager_name: str, year: str | None
) -> tuple[Response, int]:
    """Endpoint to get summary statistics for a specific manager.

    Args:
        manager_name: The name of the manager.
        year: Optional year to filter the summary stats. Defaults to all-time.

    Returns:
        Flask Response: JSON payload (manager summary or error) and status code.
    """
    try:
        data = get_manager_summary(manager_name, year)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    response = jsonify(data)

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@app.route(
    "/api/managers/<string:manager_name>/head-to-head/<string:opponent_name>",
    defaults={"year": None},
    methods=["GET"],
)
@app.route(
    "/api/managers/"
    "<string:manager_name>/head-to-head/<string:opponent_name>/<string:year>",
    methods=["GET"],
)
def manager_head_to_head(
    manager_name: str, opponent_name: str, year: str | None
) -> tuple[Response, int]:
    """Endpoint to get head-to-head statistics between two managers.

    Args:
        manager_name: The name of the first manager.
        opponent_name: The name of the opponent manager.
        year: Optional year to filter the head-to-head stats.
            Defaults to all-time.

    Returns:
        Flask Response: JSON payload (head-to-head stats or error)
        and status code.
    """
    try:
        data = get_head_to_head(
            manager_name, opponent_name, year
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    response = jsonify(data)

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@app.route(
    "/api/managers/<string:manager_name>/transactions",
    defaults={"year": None},
    methods=["GET"],
)
@app.route(
    "/api/managers/<string:manager_name>/transactions/<string:year>",
    methods=["GET"],
)
def manager_transactions(
    manager_name: str, year: str | None
) -> tuple[Response, int]:
    """Endpoint to get transaction history for a specific manager.

    Args:
        manager_name: The name of the manager.
        year: Optional year to filter transactions. Defaults to all-time.

    Returns:
        Flask Response: JSON payload (transaction history or error)
        and status code.
    """
    # Convert 'all' strings to None for proper filtering
    if year == "all":
        year = None

    try:
        data = get_manager_transactions(
            manager_name, year
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    response = jsonify(data)

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@app.route("/api/managers/<string:manager_name>/awards", methods=["GET"])
def manager_awards(manager_name: str) -> tuple[Response, int]:
    """Endpoint to get awards and recognitions for a specific manager.

    Args:
        manager_name: The name of the manager.

    Returns:
        Flask Response: JSON payload (manager awards or error) and status code.
    """
    try:
        data = get_manager_awards(manager_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    response = jsonify(data)

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


def parse_arguments(
    arg1: str | None, arg2: str | None, arg3: str | None
) -> tuple[int | None, int | None, str | None]:
    """Parse provided arguments into year, week, and manager.

    Args:
        arg1 (str | None): Season (year) or week number or manager name.
        arg2 (str | None): Season (year) or week number or manager name.
        arg3 (str | None): Season (year) or week number or manager name.

    Returns:
        tuple[int | None, int | None, str | None]: Year, week, and manager.

    Raises:
        ValueError: If multiple arguments of the same type are provided
            or invalid.
    """
    # Initialize result values
    year = None
    manager = None
    week = None

    # Iterate through all provided arguments and classify each
    for arg in (arg1, arg2, arg3):
        if arg is None:
            continue

        # Numeric arguments: check if it's a year or week
        if arg.isnumeric():
            arg_int = int(arg)
            # Check if it matches a known league year
            if arg_int in LEAGUE_IDS:
                if year is not None:
                    raise ValueError("Multiple year arguments provided.")
                year = arg_int
            # Check if it's a valid week number (1-17)
            elif 1 <= arg_int <= 17:
                if week is not None:
                    raise ValueError("Multiple week arguments provided.")
                week = arg_int
            else:
                raise ValueError("Invalid integer argument provided.")
        else:
            # Non-numeric arguments: check if it's a manager name
            if arg in NAME_TO_MANAGER_USERNAME:
                if manager is not None:
                    raise ValueError("Multiple manager arguments provided.")
                manager = arg
                continue
            else:
                raise ValueError(f"Invalid argument provided: {arg}")

    # Validate that week is only provided with year (week alone is ambiguous)
    if week is not None and year is None:
        raise ValueError("Week provided without a corresponding year.")

    return year, week, manager


def _flatten_dict(
    d: dict[Any, Any], parent_key: str = "", sep: str = "."
) -> dict[str, Any]:
    """Recursively flatten a nested dict into a single-level dict.

    Keys are concatenated with the provided separator. Non-dict values are
    copied directly. Non-dict inputs yield an empty dict.

    Args:
        d: Nested dict to flatten. If not a dict, returns an empty dict.
        parent_key: Prefix carried through recursive calls.
        sep: Separator for concatenated keys.

    Returns:
        Flattened dictionary.
    """
    out = {}

    if not isinstance(d, dict):
        return out

    # Safe iteration: handles None/non-dict inputs gracefully
    for k, v in (d or {}).items():
        # Build nested key path using separator
        nk = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            # Recurse into nested dicts to flatten deeper levels
            out.update(_flatten_dict(v, nk, sep))
        else:
            # Leaf value: add to output with full key path
            out[nk] = v
    return out


def _to_records(data: Any, key_name: str = "key") -> list[dict[str, Any]]:
    """Normalize mixed dict/list structures into a list of record dicts.

    - Lists of dicts -> flattened dict per item.
    - Dicts -> each key becomes a record; nested dict/list values are expanded.
    - Scalars -> wrapped into a single record.

    Args:
        data: Input structure.
        key_name: Field name to assign original dict keys.

    Returns:
        List of normalized record dictionaries.
    """
    # Handle list inputs: flatten each item
    if isinstance(data, list):
        for item in data:
            return (
                [_flatten_dict(item)]
                if isinstance(item, dict)
                else [{"value": item}]
            )

    # Handle dict inputs: convert to list of records with key field
    if isinstance(data, dict):
        rows = []
        for k, v in data.items():
            if isinstance(v, list):
                # Expand list values: create one record per list item
                for item in v:
                    row = {key_name: k}
                    row.update(
                        _flatten_dict(item)
                        if isinstance(item, dict)
                        else {"value": item}
                    )
                    rows.append(row)
            elif isinstance(v, dict):
                # Nested dict: flatten and merge into record
                row = {key_name: k}
                row.update(_flatten_dict(v))
                rows.append(row)
            else:
                # Scalar value: simple key-value record
                rows.append({key_name: k, "value": v})

        # Sort records alphabetically by key field for consistent ordering
        rows.sort(key=lambda item: item.get(key_name, ""), reverse=False)

        return rows

    # Fallback for scalar inputs: wrap in single-item list
    return [{"value": data}]


if __name__ == "__main__":
    from os import getenv

    # Run app
    app.run(host="0.0.0.0", port=int(getenv("PORT", "8080")))
