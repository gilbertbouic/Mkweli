# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secure_key')
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'site.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.routes import auth, main, sanctions
    from app.clients import clients
    
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(sanctions)
    app.register_blueprint(clients)
    
    # Initialize sanctions service
    with app.app_context():
        from .sanctions_service import init_sanctions_service
        try:
            init_msg = init_sanctions_service()
            print(f"✅ {init_msg}")
        except Exception as e:
            print(f"❌ Failed to initialize sanctions service: {e}")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('error.html', message='Page not found.'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('error.html', message='Internal error—please try again.'), 500
    
    return app
