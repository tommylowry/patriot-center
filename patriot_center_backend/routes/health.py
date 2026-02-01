"""Health and liveness checks."""

from flask import Blueprint, Response, jsonify

bp = Blueprint("health", __name__)


@bp.route("/")
def index_route() -> tuple[Response, int]:
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


@bp.route("/ping")
def ping_route() -> tuple[str, int]:
    """Liveness check endpoint.

    Returns:
        "pong" and 200
    """
    return "pong", 200


@bp.route("/health")
def health_route() -> tuple[Response, int]:
    """Health check endpoint.

    Returns:
        Response in JSON format with "status": "healthy" and 200
    """
    return jsonify({"status": "healthy"}), 200
