#!/usr/bin/env python3
"""
Mkweli AML Screening System - Robust Version
"""
import os
import json
import hashlib
from io import BytesIO
from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import wraps
from datetime import datetime, date
from markupsafe import escape

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
    matches_found = db.Column(db.Integer, default=0)
    match_details = db.Column(db.Text)  # JSON string of match results
    screening_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    report_hash = db.Column(db.String(64))  # SHA256 hash for verification
    ip_address = db.Column(db.String(64))

    def to_dict(self):
        return {
            'id': self.id,
            'client_name': self.client_name,
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
        else:
            client_name = request.form.get('primary_name', '').strip()
        
        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        # Use the enhanced sanctions service for matching
        from app.enhanced_matcher import get_matcher_instance
        
        matcher = get_matcher_instance()
        matches = matcher.find_matches(client_name, threshold=70)
        
        screening_time = datetime.utcnow()
        
        # Save screening report if user is logged in
        if 'user_id' in session:
            # Create report hash
            report_data = f"{client_name}{screening_time.isoformat()}{len(matches)}"
            report_hash = hashlib.sha256(report_data.encode()).hexdigest()
            
            # Save to database (client_type removed)
            report = ScreeningReport(
                user_id=session['user_id'],
                client_name=client_name,
                matches_found=len(matches),
                match_details=json.dumps(matches[:5]) if matches else None,
                screening_time=screening_time,
                report_hash=report_hash,
                ip_address=request.remote_addr
            )
            db.session.add(report)
            db.session.commit()
        
        # Return results (client_type removed)
        return jsonify({
            'client_name': client_name,
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
    """Export individual report as print-friendly HTML page (native browser print)"""
    report = ScreeningReport.query.get_or_404(report_id)
    
    # Parse match details if available
    match_details_html = ''
    if report.match_details:
        try:
            matches = json.loads(report.match_details)
            if matches:
                match_details_html = '<ul class="matches-list">'
                for match in matches:
                    matched_name = escape(match.get('matched_name', 'N/A'))
                    score = match.get('score', 0)
                    entity = match.get('entity', {})
                    source = escape(entity.get('source', 'N/A'))
                    entity_type = escape(entity.get('type', 'unknown'))
                    match_details_html += f'''
                        <li>
                            <strong>{matched_name}</strong> (Score: {score}%)<br>
                            <small>Source: {source} | Type: {entity_type}</small>
                        </li>
                    '''
                match_details_html += '</ul>'
            else:
                match_details_html = '<p>No matches found.</p>'
        except json.JSONDecodeError:
            match_details_html = '<p>No matches found.</p>'
    else:
        match_details_html = '<p>No matches found.</p>' if report.matches_found == 0 else f'<p>{report.matches_found} potential match(es) detected.</p>'
    
    # Escape user-provided data to prevent XSS
    client_name_escaped = escape(report.client_name)
    report_hash_escaped = escape(report.report_hash or 'N/A')
    
    # Generate print-friendly HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Screening Report - {client_name_escaped}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            @media print {{
                body {{ margin: 0; padding: 20px; }}
                .no-print {{ display: none !important; }}
            }}
            body {{
                font-family: Arial, sans-serif;
                padding: 40px;
                max-width: 800px;
                margin: 0 auto;
                color: #333;
            }}
            h1 {{
                color: #561217;
                border-bottom: 2px solid #561217;
                padding-bottom: 10px;
            }}
            .header {{
                margin-bottom: 30px;
            }}
            .info-row {{
                margin: 15px 0;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 4px;
            }}
            .info-label {{
                font-weight: bold;
                color: #561217;
                width: 150px;
                display: inline-block;
            }}
            .matches-section {{
                margin-top: 30px;
                padding: 20px;
                background: #fff5f5;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }}
            .matches-list {{
                list-style: none;
                padding: 0;
            }}
            .matches-list li {{
                margin: 15px 0;
                padding: 10px;
                background: white;
                border-left: 4px solid #dc3545;
                border-radius: 4px;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                font-size: 0.85em;
                color: #666;
            }}
            .hash {{
                font-family: monospace;
                word-break: break-all;
                font-size: 0.8em;
            }}
            .print-btn {{
                background: #561217;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                margin-bottom: 20px;
            }}
            .print-btn:hover {{
                background: #6b1b22;
            }}
        </style>
    </head>
    <body>
        <button class="print-btn no-print" onclick="window.print()">
            <i class="fas fa-print"></i> Print Report
        </button>
        
        <div class="header">
            <h1>Mkweli AML Screening Report</h1>
            <p>Generated: {datetime.utcnow().strftime('%m.%d.%Y %H:%M:%S UTC')}</p>
        </div>
        
        <div class="info-row">
            <span class="info-label">Client Name:</span> {client_name_escaped}
        </div>
        <div class="info-row">
            <span class="info-label">Screening Date:</span> {report.screening_time.strftime('%m.%d.%Y %H:%M:%S UTC') if report.screening_time else 'N/A'}
        </div>
        <div class="info-row">
            <span class="info-label">Matches Found:</span> {report.matches_found}
        </div>
        
        <div class="matches-section">
            <h3>Match Details</h3>
            {match_details_html}
        </div>
        
        <div class="footer">
            <p><strong>Report Hash (SHA256):</strong></p>
            <p class="hash">{report_hash_escaped}</p>
            <p>This report was generated by Mkweli AML Screening System.</p>
        </div>
        
        <script>
            // Auto-print when page loads (optional - commented out)
            // window.onload = function() {{ window.print(); }}
        </script>
    </body>
    </html>
    """
    
    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html'
    return response


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


@app.route('/api/reports/clear-today', methods=['DELETE'])
@login_required
def api_clear_today_reports():
    """Clear only today's reports with confirmation"""
    confirm = request.args.get('confirm', 'false').lower() == 'true'
    
    if not confirm:
        return jsonify({'error': 'Confirmation required. Add ?confirm=true to proceed.'}), 400
    
    today = date.today()
    count = ScreeningReport.query.filter(
        db.func.date(ScreeningReport.screening_time) == today
    ).count()
    
    ScreeningReport.query.filter(
        db.func.date(ScreeningReport.screening_time) == today
    ).delete(synchronize_session=False)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Cleared {count} screening reports from today.'
    })


@app.route('/api/reports/clear-month', methods=['DELETE'])
@login_required
def api_clear_month_reports():
    """Clear only this month's reports with confirmation"""
    confirm = request.args.get('confirm', 'false').lower() == 'true'
    
    if not confirm:
        return jsonify({'error': 'Confirmation required. Add ?confirm=true to proceed.'}), 400
    
    today = date.today()
    first_of_month = today.replace(day=1)
    
    count = ScreeningReport.query.filter(
        db.func.date(ScreeningReport.screening_time) >= first_of_month
    ).count()
    
    ScreeningReport.query.filter(
        db.func.date(ScreeningReport.screening_time) >= first_of_month
    ).delete(synchronize_session=False)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Cleared {count} screening reports from this month.'
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


@app.route('/api/sanctions/reload', methods=['POST'])
@login_required
def api_reload_sanctions():
    """Manually reload sanctions data from XML files"""
    try:
        from app.sanctions_service import reload_sanctions_data, get_sanctions_stats
        msg = reload_sanctions_data()
        stats = get_sanctions_stats()
        return jsonify({
            'success': True,
            'message': msg,
            'count': stats.get('total_entities', 0),
            'last_loaded': stats.get('last_loaded')
        })
    except Exception as e:
        return jsonify({'error': f'Failed to reload sanctions: {str(e)}'}), 500


@app.route('/api/sanctions/last-loaded')
@login_required
def api_sanctions_last_loaded():
    """Get when sanctions data was last loaded"""
    try:
        from app.sanctions_service import get_sanctions_stats
        stats = get_sanctions_stats()
        last_loaded = stats.get('last_loaded')
        
        # Format as mm.dd.yyyy if available
        formatted_date = None
        if last_loaded:
            try:
                from datetime import datetime as dt
                if isinstance(last_loaded, str):
                    loaded_dt = dt.fromisoformat(last_loaded)
                else:
                    loaded_dt = last_loaded
                formatted_date = loaded_dt.strftime('%m.%d.%Y')
            except (ValueError, AttributeError):
                formatted_date = last_loaded
        
        return jsonify({
            'last_loaded': last_loaded,
            'formatted': formatted_date
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
