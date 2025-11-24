# routes.py - Defines blueprints/routes. Import forms/models/utils (flat; no app).
from flask import Blueprint, render_template, redirect, url_for, flash, session, request, current_app
from functools import wraps
from forms import LoginForm, UserDetailsForm
from models import User, UserDetails
from extensions import db
from utils import update_sanctions_lists
from flask import jsonify
from datetime import datetime
from app.sanctions_service import screen_entity, get_sanctions_stats
from app.sanctions_service import reload_sanctions_data

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            password = request.form.get('password')
            # Hardcoded username since we only have one admin user
            user = User.query.filter_by(username='admin').first()
            if user and user.check_password(password):
                session['user_id'] = user.id
                flash('Login successful!', 'success')
                return redirect(request.args.get('next') or url_for('main.dashboard'))
            flash('Invalid master password.', 'error')
        except Exception as e:
            flash('Login error—try again.', 'error')
    
    # For GET requests or failed POST, show login form
    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.', 'success')
    return redirect(url_for('auth.login'))  # Changed to redirect to login

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Redirect to login page instead of going directly to client screening
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/check_sanctions', methods=['POST'])
def check_sanctions():
    """Check client against sanctions lists"""
    try:
        data = request.get_json()
        client_name = data.get('name', '').strip()
        client_type = data.get('type', '').strip().lower()  # 'individual' or 'company'
        
        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        # Determine entity type for optimal matching
        entity_type = None
        if client_type in ['individual', 'person']:
            entity_type = 'individual'
        elif client_type in ['company', 'organization', 'corporation', 'business']:
            entity_type = 'company'
        
        # Screen against sanctions
        matches = screen_entity(client_name, entity_type, threshold=80)
        
        result = {
            'client_name': client_name,
            'client_type': entity_type or 'unknown',
            'match_count': len(matches),
            'matches': matches[:5],  # Return top 5 matches
            'screening_time': datetime.utcnow().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Screening failed: {str(e)}'}), 500

@main.route('/reload-sanctions', methods=['POST'])
@login_required
def reload_sanctions():
    """Force reload sanctions data after file updates"""
    try:
        msg = reload_sanctions_data()
        flash(msg, 'success')
    except Exception as e:
        flash(f'Failed to reload sanctions: {str(e)}', 'error')
    return redirect(url_for('main.dashboard'))

# Add a new route for sanctions statistics
@main.route('/sanctions-stats')
def sanctions_stats():
    """Get sanctions list statistics"""
    stats = get_sanctions_stats()
    return jsonify(stats)
# Add reports route
@main.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

sanctions = Blueprint('sanctions', __name__)

@sanctions.route('/update_lists', methods=['POST'])
@login_required
def update_lists():
    try:
        data = update_sanctions_lists()
        session['sanctions_data'] = data
        flash('Updated successfully.', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception:
        flash('Error—try again.', 'error')
    return redirect(url_for('main.sanctions_lists'))
