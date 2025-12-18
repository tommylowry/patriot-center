"""
Flask application for the Patriot Center backend API.

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
from flask import Flask, jsonify, request
from flask_cors import CORS
from patriot_center_backend.constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME

app = Flask(__name__)

# Configure CORS for production (Netlify frontend)
CORS(app, resources={
    r"/get_aggregated_players*": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/get_starters*": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/get_aggregated_managers*": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/players/list": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/valid_options*": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/get_player_manager_aggregation*": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/get/managers/list": {"origins": ["https://patriotcenter.netlify.app"]},
    r"/api/managers/*": {"origins": ["https://patriotcenter.netlify.app"]},
})
CORS(app)  # Enable CORS for all routes during development

@app.route('/')
def index():
    """Root endpoint with basic info."""
    return jsonify({
        "service": "Patriot Center Backend",
        "version": "1.0.0",
        "endpoints": [
            "/get_starters",
            "/get_aggregated_players",
            "/get_aggregated_managers/<player>",
            "/valid_options",
            "/players/list",
            "/get/managers/list",
            "/api/managers/<manager_name>/summary",
            "/api/managers/<manager_name>/yearly/<year>",
            "/api/managers/<manager_name>/head-to-head/<opponent_name>",
            "/api/managers/<manager_name>/transactions",
            "/api/managers/<manager_name>/awards",
            "/ping",
            "/health"
        ]
    }), 200

@app.route('/ping')
def ping():
    """Liveness check endpoint."""
    return "pong", 200

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200

# Multiple route variants allow optional path parameters (year, manager, week)
@app.route('/get_starters', defaults={'arg1': None, 'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/get_starters/<string:arg1>', defaults={'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/get_starters/<string:arg1>/<string:arg2>', defaults={'arg3': None}, methods=['GET'])
@app.route('/get_starters/<string:arg1>/<string:arg2>/<string:arg3>', methods=['GET'])
def get_starters(arg1, arg2, arg3):
    """
    Fetch starters filtered by optional season (year), manager, and week.

    Path arguments are positional and inferred by type/value:
    - League IDs -> season
    - Week numbers 1-17 -> week
    - Known manager names -> manager

    Query param: format=json returns raw shape; otherwise flattened records.

    Returns:
        Flask Response: JSON payload (filtered starters or error).
    """
    from patriot_center_backend.services.managers import fetch_starters

    # Parse positional arguments to determine filter values
    year, week, manager = parse_arguments(arg1, arg2, arg3)

    # Fetch filtered starters data from cache
    data = fetch_starters(season=year, manager=manager, week=week)

    # Return either nested JSON or flattened records based on format parameter
    if request.args.get("format") == "json":
        return jsonify(data), 200
    return jsonify(_to_records(data)), 200

@app.route('/get_aggregated_players', defaults={'arg1': None, 'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/get_aggregated_players/<string:arg1>', defaults={'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/get_aggregated_players/<string:arg1>/<string:arg2>', defaults={'arg3': None}, methods=['GET'])
@app.route('/get_aggregated_players/<string:arg1>/<string:arg2>/<string:arg3>', methods=['GET'])
def get_aggregated_players(arg1, arg2, arg3):
    """
    Aggregate player totals (points, games started, ffWAR) for a manager.

    Uses same positional inference rules as get_starters. Returns either raw
    aggregation or flattened record list.

    Returns:
        Flask Response: JSON payload (aggregated player stats or error).
    """
    from patriot_center_backend.services.aggregated_data import fetch_aggregated_players
    
    try:
        year, week, manager = parse_arguments(arg1, arg2, arg3)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    data = fetch_aggregated_players(season=year, manager=manager, week=week)
    if request.args.get("format") == "json":
        return jsonify(data), 200
    return jsonify(_to_records(data)), 200

@app.route('/get_aggregated_managers/<string:player>', defaults={'arg2': None, 'arg3': None}, methods=['GET'])
@app.route('/get_aggregated_managers/<string:player>/<string:arg2>', defaults={'arg3': None}, methods=['GET'])
@app.route('/get_aggregated_managers/<string:player>/<string:arg2>/<string:arg3>', methods=['GET'])
def get_aggregated_managers(player, arg2, arg3):
    """
    Aggregate manager totals (points, games started, ffWAR) for a given player.

    Player name comes first as a required path component. Remaining args are
    interpreted as season and/or week. Underscores are converted to spaces to
    allow URL-friendly player names.

    Returns:
        Flask Response: JSON payload (aggregated manager stats or error).
    """
    from patriot_center_backend.services.aggregated_data import fetch_aggregated_managers

    try:
        year, week, _ = parse_arguments(arg2, arg3, None)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    player = player.replace("_", " ").replace("%27", "'")

    data = fetch_aggregated_managers(player=player, season=year, week=week)
    if request.args.get("format") == "json":
        return jsonify(data), 200
    return jsonify(_to_records(data, key_name="player")), 200

@app.route('/get_player_manager_aggregation/<string:player>/<string:manager>', defaults={'year': None, 'week': None}, methods=['GET'])
@app.route('/get_player_manager_aggregation/<string:player>/<string:manager>/<string:year>', defaults={'week': None}, methods=['GET'])
@app.route('/get_player_manager_aggregation/<string:player>/<string:manager>/<string:year>/<string:week>', methods=['GET'])
def get_player_manager_aggregation(player, manager, year, week):
    """
    Aggregate totals for a specific player-manager pairing.

    Player and manager are required path components. Remaining args are
    interpreted as season and/or week. Underscores are converted to spaces
    to allow URL-friendly player names.

    Returns:
        Flask Response: JSON payload (aggregated stats or error).
    """
    from patriot_center_backend.services.aggregated_data import fetch_player_manager_aggregation

    player = player.replace("_", " ").replace("%27", "'")

    data = fetch_player_manager_aggregation(player=player, manager=manager, season=year, week=week)
    if request.args.get("format") == "json":
        return jsonify(data), 200
    return jsonify(_to_records(data, key_name="manager")), 200

@app.route('/players/list', methods=['GET'])
def list_players():
    """
    Endpoint to list all players in the system.
    """
    from patriot_center_backend.services.players import fetch_players
    players_data = fetch_players()
    if request.args.get("format") == "json":
        return jsonify(players_data), 200
    return jsonify(_to_records(players_data, key_name="name")), 200

@app.route('/valid_options', defaults={'arg1': None, 'arg2': None, 'arg3': None, 'arg4': None}, methods=['GET'])
@app.route('/valid_options/<string:arg1>', defaults={'arg2': None, 'arg3': None, 'arg4': None}, methods=['GET'])
@app.route('/valid_options/<string:arg1>/<string:arg2>', defaults={'arg3': None, 'arg4': None}, methods=['GET'])
@app.route('/valid_options/<string:arg1>/<string:arg2>/<string:arg3>', defaults={'arg4': None}, methods=['GET'])
@app.route('/valid_options/<string:arg1>/<string:arg2>/<string:arg3>/<string:arg4>', methods=['GET'])
def valid_options(arg1, arg2, arg3, arg4):
    """
    Endpoint to validate provided season, week, manager, player, and position combinations.
    """
    from patriot_center_backend.services.valid_options import ValidOptionsService
    try:
        options = ValidOptionsService(arg1, arg2, arg3, arg4)
        data = options.get_valid_options()
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(data), 200


@app.route('/get/managers/list', methods=['GET'])
def list_managers():
    """
    Endpoint to list all managers in the system and their top-level info.
    """

    from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

    manager_metadata_manager = ManagerMetadataManager()

    try:
        data = manager_metadata_manager.get_managers_list()
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify(data), 200


@app.route('/api/managers/<string:manager_name>/summary', defaults={'year': None}, methods=['GET'])
@app.route('/api/managers/<string:manager_name>/summary/<string:year>', methods=['GET'])
def manager_summary(manager_name, year):
    """
    Endpoint to get a summary of a specific manager's performance.

    Args:
        manager_name (str): The name of the manager.
        year (str | None): Optional year to filter the summary.

    Returns:
        Flask Response: JSON payload (manager summary or error).
    """

    from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

    manager_metadata_manager = ManagerMetadataManager()

    try:
        data = manager_metadata_manager.get_manager_summary(manager_name, year)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(data), 200


@app.route('/api/managers/<string:manager_name>/yearly/<string:year>', methods=['GET'])
def manager_yearly_data(manager_name, year):
    """
    Endpoint to get detailed yearly data for a specific manager.

    Args:
        manager_name (str): The name of the manager.
        year (str): The year to filter the details.

    Returns:
        Flask Response: JSON payload (manager yearly details or error).
    """

    from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

    manager_metadata_manager = ManagerMetadataManager()

    try:
        data = manager_metadata_manager.get_manager_yearly_data(manager_name, year)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(data), 200


@app.route('/api/managers/<string:manager_name>/head-to-head/<string:opponent_name>', defaults={'year': None}, methods=['GET'])
@app.route('/api/managers/<string:manager_name>/head-to-head/<string:opponent_name>/<string:year>', methods=['GET'])
def manager_head_to_head(manager_name, opponent_name, year):
    """
    Endpoint to get head-to-head statistics between two managers.

    Args:
        manager_name (str): The name of the first manager.
        opponent_name (str): The name of the opponent manager.
        year (str | None): Optional year to filter the head-to-head stats.

    Returns:
        Flask Response: JSON payload (head-to-head stats or error).
    """

    from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

    manager_metadata_manager = ManagerMetadataManager()

    try:
        data = manager_metadata_manager.get_head_to_head(manager_name, opponent_name, year)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(data), 200


@app.route('/api/managers/<string:manager_name>/transactions', defaults={'year': None, 'type': None, 'limit': 50, 'offset': 0}, methods=['GET'])
@app.route('/api/managers/<string:manager_name>/transactions/<string:year>', defaults={'type': None, 'limit': 50, 'offset': 0}, methods=['GET'])
@app.route('/api/managers/<string:manager_name>/transactions/<string:year>/<string:type>', defaults={'limit': 50, 'offset': 0}, methods=['GET'])
@app.route('/api/managers/<string:manager_name>/transactions/<string:year>/<string:type>/<int:limit>', defaults={'offset': 0}, methods=['GET'])
@app.route('/api/managers/<string:manager_name>/transactions/<string:year>/<string:type>/<int:limit>/<int:offset>', methods=['GET'])
def manager_transactions(manager_name, year, type, limit, offset):
    """
    Endpoint to get transaction history for a specific manager.

    Args:
        manager_name (str): The name of the manager.
        year (str | None): Optional year to filter transactions.
        type (str | None): Optional transaction type to filter.
        limit (int): Number of records to return.
        offset (int): Offset for pagination.

    Returns:
        Flask Response: JSON payload (transaction history or error).
    """

    from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

    manager_metadata_manager = ManagerMetadataManager()

    try:
        data = manager_metadata_manager.get_manager_transactions(manager_name, year, type, limit, offset)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(data), 200


@app.route('/api/managers/<string:manager_name>/awards', methods=['GET'])
def manager_awards(manager_name):
    """
    Endpoint to get awards and recognitions for a specific manager.

    Args:
        manager_name (str): The name of the manager.

    Returns:
        Flask Response: JSON payload (manager awards or error).
    """

    from patriot_center_backend.utils.manager_metadata_manager import ManagerMetadataManager

    manager_metadata_manager = ManagerMetadataManager()

    try:
        data = manager_metadata_manager.get_manager_awards(manager_name)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(data), 200

    
# /update_caches endpoint removed - cache updates now handled by GitHub Actions
# See .github/workflows/update-cache.yml

def parse_arguments(arg1, arg2, arg3):
    """
    Infer season (year), week, and manager from up to three positional args.

    Resolution order:
    - Integers matching LEAGUE_IDS -> season
    - Integers 1-17 -> week
    - Strings matching NAME_TO_MANAGER_USERNAME -> manager
    - Rejects duplicates or ambiguous assignments.

    Args:
        arg1, arg2, arg3 (str | None): Raw path segments.

    Returns:
        tuple: (season:int|None, week:int|None, manager:str|None)

    Raises:
        ValueError: On invalid values, duplicates, or week without season.
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
        if arg.isnumeric() == True:
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

def _flatten_dict(d, parent_key="", sep="."):
    """
    Recursively flatten a nested dict into a single-level dict.

    Keys are concatenated with the provided separator. Non-dict values are
    copied directly. Non-dict inputs yield an empty dict.

    Args:
        d (dict | any): Potentially nested dictionary to flatten.
        parent_key (str): Prefix carried through recursive calls.
        sep (str): Separator for concatenated keys.

    Returns:
        dict: Flattened dictionary.
    """
    out = {}
    # Safe iteration: handles None/non-dict inputs gracefully
    for k, v in (d or {}).items() if isinstance(d, dict) else []:
        # Build nested key path using separator
        nk = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            # Recurse into nested dicts to flatten deeper levels
            out.update(_flatten_dict(v, nk, sep))
        else:
            # Leaf value: add to output with full key path
            out[nk] = v
    return out

def _to_records(data, key_name="key"):
    """
    Normalize mixed dict/list structures into a list of record dicts.

    - Lists of dicts -> flattened dict per item.
    - Dicts -> each key becomes a record; nested dict/list values are expanded.
    - Scalars -> wrapped into a single record.

    Args:
        data (dict | list | any): Input structure.
        key_name (str): Field name to assign original dict keys.

    Returns:
        list[dict]: List of normalized record dictionaries.
    """
    # Handle list inputs: flatten each item
    if isinstance(data, list):
        return [(_flatten_dict(x) if isinstance(x, dict) else {"value": x}) for x in data]

    # Handle dict inputs: convert to list of records with key field
    if isinstance(data, dict):
        rows = []
        for k, v in data.items():
            if isinstance(v, list):
                # Expand list values: create one record per list item
                for item in v:
                    row = {key_name: k}
                    row.update(_flatten_dict(item) if isinstance(item, dict) else {"value": item})
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
        rows.sort(key=lambda x: x.get(key_name, ""), reverse=False)

        return rows

    # Fallback for scalar inputs: wrap in single-item list
    return [{"value": data}]

if __name__ == '__main__':
    from os import getenv
    app.run(host="0.0.0.0", port=int(getenv("PORT", "8080")))