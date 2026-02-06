"""Routes for the Patriot Center API."""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Register blueprints for the Patriot Center API.

    Args:
        app: The Flask application.
    """
    from patriot_center_backend.routes.aggregation import bp as aggregation_bp
    from patriot_center_backend.routes.health import bp as health_bp
    from patriot_center_backend.routes.managers import bp as managers_bp
    from patriot_center_backend.routes.options import bp as options_bp

    app.register_blueprint(aggregation_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(managers_bp)
    app.register_blueprint(options_bp)
