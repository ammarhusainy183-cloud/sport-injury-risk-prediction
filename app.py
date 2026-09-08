from flask import Flask, render_template, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os
from config import config
from models import db
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.exercises import exercise_bp
from routes.risk import risk_bp
from routes.coach import coach_bp

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(exercise_bp)
    app.register_blueprint(risk_bp)
    app.register_blueprint(coach_bp)
    
    # Application routes
    @app.route("/")
    def index():
        # Render landing/login page; the dashboard remains at the same path after login
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html")
    
    @app.route("/api/health", methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Sport Injury Risk Prediction Portal is running'}), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

# Create app instance
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == "__main__":
    debug_mode = os.environ.get('FLASK_DEBUG', '0').lower() in {'1', 'true', 'yes', 'on'}
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', '5000')),
        use_reloader=debug_mode
    )