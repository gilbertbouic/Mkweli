# routes.py - Defines blueprints/routes. Import forms/models/utils (flat; no app).
from flask import Blueprint, render_template, redirect, url_for, flash, session, request, current_app
from functools import wraps
from forms import LoginForm, UserDetailsForm
from models import User, UserDetails
from extensions import db
from utils import update_sanctions_lists

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

@main.route('/sanctions-lists')
@login_required
def sanctions_lists():
    data = session.get('sanctions_data', {})
    return render_template('screening.html')  # Changed to screening.html

@main.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = User.query.get(session['user_id'])
    form = UserDetailsForm()
    
    if form.validate_on_submit():
        try:
            if not user.user_details:
                user_details = UserDetails(
                    user_id=user.id,
                    org_company=form.org_company.data,
                    address=form.address.data,
                    phone=form.phone.data,
                    tax_reg=form.tax_reg.data
                )
                db.session.add(user_details)
            else:
                user.user_details.org_company = form.org_company.data
                user.user_details.address = form.address.data
                user.user_details.phone = form.phone.data
                user.user_details.tax_reg = form.tax_reg.data
            db.session.commit()
            flash('Settings saved successfully!', 'success')
            return redirect(url_for('main.settings'))
        except ValueError as e:
            flash(f'Validation error: {str(e)}', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error saving settings—try again.', 'error')
    elif request.method == 'GET' and user.user_details:
        form.org_company.data = user.user_details.org_company
        form.address.data = user.user_details.address
        form.phone.data = user.user_details.phone
        form.tax_reg.data = user.user_details.tax_reg
    
    return render_template('settings.html', form=form)

@main.route('/check_sanctions', methods=['POST'])
def check_sanctions():
    """Quick name check against sanctions lists (public API)."""
    from flask import jsonify
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Name required'}), 400
        
        name = data['name'].strip()
        if not name or len(name) < 2:
            return jsonify({'error': 'Name too short'}), 400
        
        # Simple fuzzy match against individuals and entities
        from fuzzywuzzy import fuzz
        from models import Individual, Entity
        threshold = 82
        matches = []
        
        # Check individuals
        for individual in Individual.query.all():
            if individual.name and fuzz.token_set_ratio(name.lower(), individual.name.lower()) >= threshold:
                matches.append({
                    'name': individual.name,
                    'type': 'Individual',
                    'source': individual.source,
                    'nationality': individual.nationality
                })
        
        # Check entities
        for entity in Entity.query.all():
            if entity.name and fuzz.token_set_ratio(name.lower(), entity.name.lower()) >= threshold:
                matches.append({
                    'name': entity.name,
                    'type': 'Entity',
                    'source': entity.source
                })
        
        return jsonify({'matches': matches})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
