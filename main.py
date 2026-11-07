"""Start the minimal LTI 1.3 external tool."""

from app import create_app
from config import load_settings


if __name__ == "__main__":
    # Load settings and start the development server.
    settings = load_settings()
    create_app().run(
        host=settings.host,
        port=settings.port,
        debug=False,
    )
