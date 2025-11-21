# routes.py - Defines blueprints/routes. Import forms/models/utils (flat; no app).
from flask import Blueprint, render_template, redirect, url_for, flash, session, request  # Added: render_template
from functools import wraps
from forms import LoginForm, UserDetailsForm  # Added
from models import User, UserDetails
from utils import update_sanctions_lists

# Decorator: Auth logic (reviewed: Secure session)
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
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                session['user_id'] = user.id
                flash('Login successful!', 'success')
                # Auto-create user details if not exist
                if not user.user_details:
                    user_details = UserDetails(user_id=user.id, org_company='', address='', phone='', tax_reg='')
                    db.session.add(user_details)
                    db.session.commit()
                return redirect(request.args.get('next') or url_for('main.dashboard'))
            flash('Invalid credentials.', 'error')
        except Exception as e:
            flash('Login error—try again.', 'error')  # User-friendly
    return render_template('login.html', form=form)  # ARIA: form aria-label="Login form"

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.', 'success')
    return redirect(url_for('main.index'))

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')  # Nav: Home > Sanctions > etc.

@main.route('/sanctions-lists')
@login_required
def sanctions_lists():
    data = session.get('sanctions_data', {})
    return render_template('sanctions_lists.html', data=data)

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
