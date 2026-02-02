"""Managers endpoints for Patriot Center."""

from typing import Literal

from flask import Blueprint, Response, jsonify

from patriot_center_backend.exporters.award_exporter import (
    get_manager_awards,
)
from patriot_center_backend.exporters.head_to_head_exporter import (
    get_head_to_head,
)
from patriot_center_backend.exporters.manager_list_exporter import (
    get_managers_list,
)
from patriot_center_backend.exporters.summary_exporter import (
    get_manager_summary,
)
from patriot_center_backend.exporters.transaction_exporter import (
    get_manager_transactions,
)

bp = Blueprint("managers", __name__)


@bp.route("/get/managers/list/<string:active_only>", methods=["GET"])
def get_managers_list_route(
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


@bp.route(
    "/api/managers/<string:manager_name>/summary",
    defaults={"year": None},
    methods=["GET"],
)
@bp.route(
    "/api/managers/<string:manager_name>/summary/<string:year>", methods=["GET"]
)
def get_manager_summary_route(
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


@bp.route(
    "/api/managers/<string:manager_name>/head-to-head/<string:opponent_name>",
    defaults={"year": None},
    methods=["GET"],
)
@bp.route(
    "/api/managers/"
    "<string:manager_name>/head-to-head/<string:opponent_name>/<string:year>",
    methods=["GET"],
)
def get_head_to_head_route(
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
        data = get_head_to_head(manager_name, opponent_name, year)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    response = jsonify(data)

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@bp.route(
    "/api/managers/<string:manager_name>/transactions",
    defaults={"year": None},
    methods=["GET"],
)
@bp.route(
    "/api/managers/<string:manager_name>/transactions/<string:year>",
    methods=["GET"],
)
def get_manager_transactions_route(
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
        data = get_manager_transactions(manager_name, year)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    response = jsonify(data)

    # Cache for 1 hour
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response, 200


@bp.route("/api/managers/<string:manager_name>/awards", methods=["GET"])
def get_manager_awards_route(manager_name: str) -> tuple[Response, int]:
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
