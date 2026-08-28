from flask import Flask
from backend.api.health import health_bp

def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_mapping(
        DATABASE_URL="sqlite:///debrix.db",
    )

    if test_config:
        app.config.update(test_config)

    app.register_blueprint(health_bp)
    return app