from flask import Flask
from backend.api.health import health_bp
from backend.api.objects import objects_bp
from backend.api.propagation import propagation_bp
from backend.api.conjunction import conjunction_bp
from backend.api.alerts import alerts_bp

def create_app(test_config=None):
    app = Flask(__name__)

    app.config.from_mapping(
        DATABASE_URL="sqlite:///debrix.db",
    )

    if test_config:
        app.config.update(test_config)

    app.register_blueprint(health_bp)
    app.register_blueprint(objects_bp)
    app.register_blueprint(propagation_bp)
    app.register_blueprint(conjunction_bp)
    app.register_blueprint(alerts_bp)
    return app