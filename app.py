"""
Flask Backend for Semantic Sentinel
Main application entry point
"""
from flask import Flask
from flask_cors import CORS
from config import Config
from database import init_db
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Register blueprints
    from routes.video_routes import video_bp
    from routes.analysis_routes import analysis_bp
    from routes.history_routes import history_bp
    
    app.register_blueprint(video_bp, url_prefix='/api/video')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(history_bp, url_prefix='/api/history')
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return {'status': 'healthy', 'message': 'Semantic Sentinel API is running'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)