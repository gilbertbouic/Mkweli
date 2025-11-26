#!/usr/bin/env python3
"""
Mkweli AML Screening System - Robust Version
"""
import os
import json
import hashlib
from io import BytesIO
from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import wraps
from datetime import datetime, date
from weasyprint import HTML

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


class ScreeningReport(db.Model):
    """Track individual client screenings with details"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_name = db.Column(db.String(255), nullable=False)
    client_type = db.Column(db.String(50))  # individual or company
    matches_found = db.Column(db.Integer, default=0)
    match_details = db.Column(db.Text)  # JSON string of match results
    screening_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    report_hash = db.Column(db.String(64))  # SHA256 hash for verification
    ip_address = db.Column(db.String(64))

    def to_dict(self):
        return {
            'id': self.id,
            'client_name': self.client_name,
            'client_type': self.client_type,
            'matches_found': self.matches_found,
            'screening_time': self.screening_time.isoformat() if self.screening_time else None,
            'report_hash': self.report_hash
        }

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
        # Accept both JSON and form data
        if request.is_json:
            data = request.get_json()
            client_name = data.get('name', '').strip()
            client_type = data.get('type', 'individual').lower()
        else:
            client_name = request.form.get('primary_name', '').strip()
            client_type = request.form.get('client_type', 'Individual').lower()
        
        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        # Use the sanctions service for matching
        from app.sanctions_service import screen_entity, fuzzy_matcher
        
        # Map client type to entity type for matching
        entity_type = None
        if client_type in ['individual', 'person']:
            entity_type = 'individual'
        elif client_type in ['company', 'organization', 'company/organization']:
            entity_type = 'company'
        
        # Screen with appropriate threshold
        matches = screen_entity(client_name, entity_type, threshold=80)
        
        screening_time = datetime.utcnow()
        
        # Save screening report if user is logged in
        if 'user_id' in session:
            # Create report hash
            report_data = f"{client_name}{entity_type}{screening_time.isoformat()}{len(matches)}"
            report_hash = hashlib.sha256(report_data.encode()).hexdigest()
            
            # Save to database
            report = ScreeningReport(
                user_id=session['user_id'],
                client_name=client_name,
                client_type=entity_type or 'unknown',
                matches_found=len(matches),
                match_details=json.dumps(matches[:5]) if matches else None,
                screening_time=screening_time,
                report_hash=report_hash,
                ip_address=request.remote_addr
            )
            db.session.add(report)
            db.session.commit()
        
        # Return results
        return jsonify({
            'client_name': client_name,
            'client_type': entity_type or 'unknown',
            'match_count': len(matches),
            'matches': matches[:5],  # Return top 5 matches
            'screening_time': screening_time.isoformat()
        })
        
    except Exception as e:
        print(f"Error in sanctions check: {e}")
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
            'status': 'error',
            'message': f'Error loading sanctions: {str(e)}'
        })

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')


# ==== API Endpoints for Reports and Dashboard ====

@app.route('/api/reports/list')
@login_required
def api_reports_list():
    """Get all screening reports (paginated)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # Limit max per page
    
    reports_query = ScreeningReport.query.order_by(ScreeningReport.screening_time.desc())
    paginated = reports_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'reports': [r.to_dict() for r in paginated.items],
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    })


@app.route('/api/reports/export/<int:report_id>')
@login_required
def api_export_report(report_id):
    """Export individual report as PDF"""
    report = ScreeningReport.query.get_or_404(report_id)
    
    # Generate PDF content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1 {{ color: #561217; }}
            .header {{ border-bottom: 2px solid #561217; padding-bottom: 10px; margin-bottom: 20px; }}
            .info {{ margin: 10px 0; }}
            .label {{ font-weight: bold; }}
            .matches {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }}
            .footer {{ margin-top: 30px; font-size: 0.8em; color: #666; border-top: 1px solid #ddd; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Mkweli AML Screening Report</h1>
            <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
        <div class="info"><span class="label">Client Name:</span> {report.client_name}</div>
        <div class="info"><span class="label">Client Type:</span> {report.client_type or 'Not specified'}</div>
        <div class="info"><span class="label">Screening Date:</span> {report.screening_time.strftime('%Y-%m-%d %H:%M:%S UTC') if report.screening_time else 'N/A'}</div>
        <div class="info"><span class="label">Matches Found:</span> {report.matches_found}</div>
        <div class="matches">
            <h3>Match Details</h3>
            <p>{'No matches found.' if report.matches_found == 0 else f'{report.matches_found} potential match(es) detected.'}</p>
        </div>
        <div class="footer">
            <p><strong>Report Hash:</strong> {report.report_hash}</p>
            <p>This report was generated by Mkweli AML Screening System.</p>
        </div>
    </body>
    </html>
    """
    
    pdf_buffer = BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'screening_report_{report_id}.pdf'
    )


@app.route('/api/reports/daily-stats')
@login_required
def api_daily_stats():
    """Get daily screening statistics"""
    today = date.today()
    
    today_count = ScreeningReport.query.filter(
        db.func.date(ScreeningReport.screening_time) == today
    ).count()
    
    today_matches = db.session.query(db.func.sum(ScreeningReport.matches_found)).filter(
        db.func.date(ScreeningReport.screening_time) == today
    ).scalar() or 0
    
    return jsonify({
        'date': today.isoformat(),
        'screenings': today_count,
        'matches': today_matches
    })


@app.route('/api/reports/monthly-stats')
@login_required
def api_monthly_stats():
    """Get monthly screening statistics"""
    today = date.today()
    first_of_month = today.replace(day=1)
    
    month_count = ScreeningReport.query.filter(
        db.func.date(ScreeningReport.screening_time) >= first_of_month
    ).count()
    
    month_matches = db.session.query(db.func.sum(ScreeningReport.matches_found)).filter(
        db.func.date(ScreeningReport.screening_time) >= first_of_month
    ).scalar() or 0
    
    return jsonify({
        'month': today.strftime('%B %Y'),
        'screenings': month_count,
        'matches': month_matches
    })


@app.route('/api/reports/clear-all', methods=['DELETE'])
@login_required
def api_clear_all_reports():
    """Clear all reports with confirmation"""
    confirm = request.args.get('confirm', 'false').lower() == 'true'
    
    if not confirm:
        return jsonify({'error': 'Confirmation required. Add ?confirm=true to proceed.'}), 400
    
    count = ScreeningReport.query.count()
    ScreeningReport.query.delete()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Cleared {count} screening reports.'
    })


@app.route('/api/dashboard/sanctions-count')
@login_required
def api_sanctions_count():
    """Get actual sanctions entity count for dashboard"""
    try:
        from app.sanctions_service import get_sanctions_stats
        stats = get_sanctions_stats()
        return jsonify({
            'count': stats.get('total_entities', 0),
            'sources': stats.get('sources', {})
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/screening-stats')
@login_required
def api_screening_stats():
    """Get today's and this month's screening counts"""
    today = date.today()
    first_of_month = today.replace(day=1)
    
    today_count = ScreeningReport.query.filter(
        db.func.date(ScreeningReport.screening_time) == today
    ).count()
    
    month_count = ScreeningReport.query.filter(
        db.func.date(ScreeningReport.screening_time) >= first_of_month
    ).count()
    
    total_count = ScreeningReport.query.count()
    
    return jsonify({
        'today': today_count,
        'this_month': month_count,
        'total': total_count
    })

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

@app.route('/sanctions-lists')
@login_required
def sanctions_lists():
    """Sanctions lists management page"""
    return render_template('sanctions_lists.html')


@app.route('/screening')
def screening():
    """Legacy screening route - removed, redirect to dashboard"""
    flash('The /screening page has been removed. Please use the Dashboard for screening.', 'info')
    return redirect(url_for('dashboard'))


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

if __name__ == '__main__':
    print("🚀 Starting Mkweli AML Screening System...")
    print("📍 Access at: http://localhost:5000")
    print("🔑 Login with password: admin123")
    # Debug mode controlled by environment variable for security
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
