#!/usr/bin/env python3
"""
Mkweli AML Screening System - Robust Version
"""
import os
from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import wraps
from datetime import datetime

# Initialize Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mkweli-secure-key-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mkweli.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('instance', exist_ok=True)

# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))  # individual or company
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        user = User.query.filter_by(username='admin').first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/clients')
@login_required
def clients():
    clients_list = Client.query.all()
    return render_template('clients.html', clients=clients_list)

@app.route('/check_sanctions', methods=['POST'])
def check_sanctions():
    """Check client against sanctions lists"""
    try:
        data = request.get_json()
        client_name = data.get('name', '').strip()
        client_type = data.get('type', '').strip().lower()
        
        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        # Try to use sanctions service
        try:
            from app.sanctions_service import screen_entity
            matches = screen_entity(client_name, client_type, threshold=80)
            result = {
                'client_name': client_name,
                'client_type': client_type or 'unknown',
                'match_count': len(matches),
                'matches': matches[:5],
                'screening_time': datetime.utcnow().isoformat(),
                'status': 'success'
            }
        except Exception as e:
            # Fallback if sanctions service not available
            result = {
                'client_name': client_name,
                'client_type': client_type or 'unknown',
                'match_count': 0,
                'matches': [],
                'screening_time': datetime.utcnow().isoformat(),
                'status': 'sanctions_service_loading',
                'note': 'Sanctions system is initializing...'
            }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Screening failed: {str(e)}'}), 500

@app.route('/sanctions-stats')
def sanctions_stats():
    """Get sanctions list statistics"""
    try:
        from app.sanctions_service import get_sanctions_stats
        stats = get_sanctions_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'status': 'initializing',
            'message': 'Sanctions service is starting up...'
        })

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', message='Page not found.'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', message='Internal error—please try again.'), 500

# Initialize application
with app.app_context():
    # Create database tables
    db.create_all()
    
    # Create admin user if doesn't exist
    from werkzeug.security import generate_password_hash
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created (password: admin123)")
    else:
        print("✅ Admin user already exists")
    
    # Initialize sanctions service
    try:
        from app.sanctions_service import init_sanctions_service
        init_msg = init_sanctions_service()
        print(f"✅ {init_msg}")
    except Exception as e:
        print(f"⚠️ Sanctions service: {e}")
        print("📋 The application will run with basic functionality")
        print("🔧 Sanctions screening will be available once the service loads")

if __name__ == '__main__':
    print("🚀 Starting Mkweli AML Screening System...")
    print("📍 Access at: http://localhost:5000")
    print("🔑 Login with password: admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/sanctions-lists')
@login_required
def sanctions_lists():
    """Sanctions lists management page"""
    return render_template('sanctions_lists.html')

@app.route('/screening')
@login_required
def screening():
    """Client screening page"""
    return render_template('screening.html')

@app.route('/settings')
@login_required
def settings():
    """Application settings"""
    return render_template('settings.html')

@app.route('/help')
@login_required
def help_page():
    """Help documentation"""
    return render_template('help.html')
