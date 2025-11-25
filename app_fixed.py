#!/usr/bin/env python3
"""
Mkweli AML Screening System - Completely Fixed Version
"""
import os
import sys
from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import wraps
from datetime import datetime

# Add app directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

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
    try:
        client_name = request.form.get('client_name', '').strip()
        client_type = request.form.get('client_type', 'Individual')
        
        print(f"🔍 Screening: '{client_name}'")
        
        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        # Use direct imports
        from robust_sanctions_parser import RobustSanctionsParser
        from advanced_fuzzy_matcher import OptimalFuzzyMatcher
        
        parser = RobustSanctionsParser()
        entities = parser.parse_all_sanctions()
        matcher = OptimalFuzzyMatcher(entities)
        matches = matcher.find_matches(client_name, threshold=70)
        
        # Return results
        return jsonify({
            'client_name': client_name,
            'client_type': client_type,
            'matches_found': len(matches),
            'matches': matches[:5],
            'screening_time': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error in sanctions check: {e}")
        return jsonify({'error': 'Screening failed'}), 500

@app.route('/sanctions-stats')
def sanctions_stats():
    """Get sanctions list statistics"""
    try:
        from robust_sanctions_parser import RobustSanctionsParser
        parser = RobustSanctionsParser()
        entities = parser.parse_all_sanctions()
        return jsonify({
            'status': 'active',
            'entities_loaded': len(entities),
            'message': f'Loaded {len(entities)} sanction entities'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        })

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

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

if __name__ == '__main__':
    print("🚀 Starting Mkweli AML Screening System...")
    print("📍 Access at: http://localhost:5000")
    print("🔑 Login with password: admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)
