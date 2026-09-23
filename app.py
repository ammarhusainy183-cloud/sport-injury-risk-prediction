from flask import Flask, render_template, jsonify, current_app
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy import text
import os

from config import config
from models import db

from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.exercises import exercise_bp
from routes.risk import risk_bp
from routes.coach import coach_bp


def create_app(config_name="development"):
    """Application factory"""

    app = Flask(__name__)

    # =========================================================
    # LOAD CONFIGURATION
    # =========================================================

    app.config.from_object(config[config_name])

    # =========================================================
    # INITIALIZE EXTENSIONS
    # =========================================================

    db.init_app(app)
    JWTManager(app)
    CORS(app)

    # =========================================================
    # REGISTER BLUEPRINTS
    # =========================================================

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(exercise_bp)
    app.register_blueprint(risk_bp)
    app.register_blueprint(coach_bp)

    # =========================================================
    # APPLICATION ROUTES
    # =========================================================

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html")

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "message": "Sport Injury Risk Prediction Portal is running"
        }), 200

    # =========================================================
    # TEMPORARY DATABASE TEST
    # =========================================================

    @app.route("/api/db-test", methods=["GET"])
    def db_test():
        """
        Temporary database diagnostic endpoint.
        Remove this endpoint after the database connection
        has been confirmed.
        """

        try:
            # Check whether DATABASE_URL exists
            database_url = os.environ.get("DATABASE_URL")

            # Get the database backend being used by SQLAlchemy
            database_type = db.engine.url.get_backend_name()

            # Count registered users
            user_count = db.session.execute(
                text("SELECT COUNT(*) FROM users")
            ).scalar()

            return jsonify({
                "status": "success",
                "database_type": database_type,
                "database_url_exists": bool(database_url),
                "database_url_prefix": (
                    database_url.split("://")[0]
                    if database_url and "://" in database_url
                    else None
                ),
                "user_count": user_count
            }), 200

        except Exception as error:
            current_app.logger.exception(
                "Database test failed"
            )

            return jsonify({
                "status": "error",
                "message": str(error)
            }), 500

    # =========================================================
    # ERROR HANDLERS
    # =========================================================

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Endpoint not found"
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal server error"
        }), 500

    # =========================================================
    # CREATE DATABASE TABLES
    # =========================================================

    with app.app_context():
        db.create_all()

    return app


# =========================================================
# CREATE APPLICATION INSTANCE
# =========================================================

app = create_app(
    os.environ.get("FLASK_ENV", "development")
)


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    debug_mode = (
        os.environ.get("FLASK_DEBUG", "0").lower()
        in {"1", "true", "yes", "on"}
    )

    app.run(
        debug=debug_mode,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        use_reloader=debug_mode
    )