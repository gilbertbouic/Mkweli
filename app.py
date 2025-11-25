#!/usr/bin/env python3
"""
Mkweli AML Screening System - Robust Version
"""
import os
import sys
from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import wraps
from datetime import datetime

# Setup path for app folder imports (sanctions parser, fuzzy matcher)
_app_folder = os.path.join(os.path.dirname(__file__), 'app')
if _app_folder not in sys.path:
    sys.path.insert(0, _app_folder)

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
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            client_name = data.get('name', '').strip()
            client_type = data.get('type', 'Individual')
        else:
            client_name = request.form.get('primary_name', '').strip()
            client_type = request.form.get('client_type', 'Individual')
        
        # Log incoming request for debugging
        print(f"[DEBUG] Received screening request:")
        print(f"  - Content-Type: {request.content_type}")
        print(f"  - Client name: '{client_name}'")
        print(f"  - Client type: '{client_type}'")
        
        if not client_name:
            print(f"[DEBUG] Error: Empty client_name received")
            return jsonify({'error': 'Client name is required'}), 400
        
        from robust_sanctions_parser import RobustSanctionsParser
        from advanced_fuzzy_matcher import OptimalFuzzyMatcher
        
        # Parse sanctions data
        parser = RobustSanctionsParser()
        entities = parser.parse_all_sanctions()
        print(f"[DEBUG] Loaded {len(entities)} sanctions entities")
        
        # Perform fuzzy matching
        matcher = OptimalFuzzyMatcher(entities)
        matches = matcher.find_matches(client_name, threshold=70)
        print(f"[DEBUG] Found {len(matches)} matches for '{client_name}'")
        
        screening_time = datetime.utcnow().isoformat()
        
        # Transform matches to match the frontend expected format
        formatted_matches = []
        for match in matches[:5]:
            formatted_matches.append({
                'matched_name': match.get('primary_name') or match.get('name', 'Unknown'),
                'score': match.get('score', 0),
                'entity': {
                    'source': match.get('source', 'Unknown'),
                    'type': match.get('type', 'entity'),
                    'list_type': match.get('list_type', ''),
                    'id': match.get('id', '')
                }
            })
        
        # Return results
        return jsonify({
            'client_name': client_name,
            'client_type': client_type,
            'match_count': len(matches),
            'matches': formatted_matches,
            'screening_time': screening_time
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[DEBUG] Error in sanctions check: {e}")
        print(f"[DEBUG] Traceback: {error_details}")
        return jsonify({'error': f'Screening failed: {str(e)}'}), 500

@app.route('/sanctions-stats')
def sanctions_stats():
    """Get sanctions list statistics"""
    try:
        from robust_sanctions_parser import RobustSanctionsParser
        parser = RobustSanctionsParser()
        entities = parser.parse_all_sanctions()
        return jsonify({
            'status': 'active',
            'total_entities': len(entities),
            'message': f'Loaded {len(entities)} sanction entities'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error loading sanctions: {str(e)}'
        })

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/debug/echo', methods=['GET', 'POST'])
def debug_echo():
    """Debug endpoint that echoes back request details"""
    result = {
        'method': request.method,
        'content_type': request.content_type,
        'headers': dict(request.headers),
        'args': dict(request.args),
        'form': dict(request.form),
    }
    
    if request.is_json:
        try:
            result['json'] = request.get_json()
        except Exception as e:
            result['json_error'] = str(e)
    else:
        result['json'] = None
    
    return jsonify(result)

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
        from robust_sanctions_parser import RobustSanctionsParser
        parser = RobustSanctionsParser()
        entities = parser.parse_all_sanctions()
        print(f"✅ Sanctions service loaded {len(entities)} entities")
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
