from flask import Flask, jsonify
from flask_cors import CORS
from config import config
import os

def create_app(env='development'):
    """Factory para criar a aplicação Flask"""
    app = Flask(__name__)
    
    app.config.from_object(config[env])
    
    from database import db
    db.init_app(app)
    
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})

    from routes import auth_bp, admin_bp, user_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    
    with app.app_context():
        db.create_all()
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'ok'}), 200
    
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'name': 'Auth API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'user': '/api/user',
                'admin': '/api/admin'
            }
        }), 200
    
    @app.errorhandler(Exception)
    def handle_error(error):
        return jsonify({'error': str(error)}), 500
    
    return app


if __name__ == '__main__':
    env = os.getenv('FLASK_ENV', 'development')
    app = create_app(env)
    
    port = int(os.getenv('PORT', 5000))
    debug = env == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
