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

import logging

from flask import Flask
from flask_cors import CORS

from patriot_center_backend.routes import register_blueprints

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
register_blueprints(app)

# Configure CORS for production (Netlify frontend)
CORS(
    app,
    resources={
        r"/get_aggregated_players*": {
            "origins": ["https://patriotcenter.netlify.app"]
        },
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


if __name__ == "__main__":
    from os import getenv

    # Run app
    app.run(host="0.0.0.0", port=int(getenv("PORT", "8080")))
