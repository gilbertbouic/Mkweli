#!/usr/bin/env python3
"""
Complete Mkweli AML System - Fixed Version
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

# Initialize Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mkweli-secure-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mkweli.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))

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

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/check_sanctions', methods=['POST'])
@login_required
def check_sanctions():
    try:
        # FIX: Use 'client_name' not 'primary_name'
        client_name = request.form.get('client_name', '').strip()
        client_type = request.form.get('client_type', 'Individual')
        
        print(f"🔍 Screening request: '{client_name}' (type: {client_type})")
        
        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        # Import and use the sanctions system
        from robust_sanctions_parser import RobustSanctionsParser
        from advanced_fuzzy_matcher import OptimalFuzzyMatcher
        
        parser = RobustSanctionsParser()
        entities = parser.parse_all_sanctions()
        matcher = OptimalFuzzyMatcher(entities)
        matches = matcher.find_matches(client_name, threshold=70)
        
        print(f"✅ Found {len(matches)} matches for '{client_name}'")
        
        return jsonify({
            'client_name': client_name,
            'client_type': client_type,
            'matches_found': len(matches),
            'matches': matches[:5],
            'screening_time': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Screening error: {e}")
        return jsonify({'error': f'Screening failed: {str(e)}'}), 500

@app.route('/sanctions-stats')
def sanctions_stats():
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
        return jsonify({'status': 'error', 'message': str(e)})

# Initialize database
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created (password: admin123)")
    else:
        print("✅ Admin user already exists")

if __name__ == '__main__':
    print("🚀 Starting Mkweli AML System...")
    print("📍 http://localhost:5000")
    print("🔑 Login with: admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)
