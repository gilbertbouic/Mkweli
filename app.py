# app.py - Core setup: Configures app, inits DB, registers blueprints. Run with 'flask run'.
# Low-tech: Flat structure; CLI-friendly. Cross-OS: Uses os for paths/env.

import os
from flask import Flask, render_template  # Added: render_template for handlers
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_secure_key')  # Security: Env var (all OS: export/set)
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'site.db')  # Cross-OS path
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'  # Fixed: Prepend 'sqlite:///' for valid URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Performance

db = SQLAlchemy(app)  # DB init (global for models/init_db)

# Import/register blueprints: Modular, no circulars (routes don't import app)
from routes import auth, main, sanctions
app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(sanctions)

# Error Handlers: Feedback/consistency
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', message='Page not found.'), 404  # Accessibility: Simple page

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', message='Internal error—please try again.'), 500

if __name__ == '__main__':
    app.run(debug=True)  # Dev; production: Use gunicorn (pip install; gunicorn app:app)
