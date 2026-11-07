"""Flask application factory."""

from flask import Flask

from config import load_settings
from routes import routes


def create_app() -> Flask:
    """Create and configure the Flask application."""
    settings = load_settings()
    app = Flask(__name__)
    app.secret_key = settings.flask_secret_key
    app.config["LTI_SETTINGS"] = settings
    app.register_blueprint(routes)
    return app
