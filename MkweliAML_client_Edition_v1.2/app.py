#!/usr/bin/env python3
"""
MkweliAML - Anti-Money Laundering Compliance System
Production version with ALL improvements
"""

import os
import sys
import hashlib
import json
import shutil
from datetime import datetime
from functools import wraps
from fuzzywuzzy import fuzz
from Levenshtein import distance

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response, send_file
from config import ProductionConfig
from database import db
from auth import AuthSystem

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

app = Flask(__name__)
app.config.from_object(ProductionConfig)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

auth_system = AuthSystem()

def sanitize_input(text):
    if text is None: return ""
    return re.sub(r'[;\"\']', '', str(text)).strip()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# Initialize DB
if not os.path.exists(app.config['DATABASE']):
    from init_db import init_database
    init_database()

# Wizard State
WIZARD_STEPS = ['password', 'list', 'client']
session['wizard_step'] = session.get('wizard_step', 0)

@app.before_request
def check_wizard():
    if not auth_system.is_password_set() and request.endpoint not in ['setup_password', 'static', 'wizard_list', 'wizard_client']:
        return redirect(url_for('setup_password'))
    if session.get('wizard_step', 0) < len(WIZARD_STEPS) and request.endpoint not in ['static', 'setup_password', 'wizard_list', 'wizard_client']:
        return redirect(url_for(f'wizard_{WIZARD_STEPS[session["wizard_step"]]}'))

# AUTH ROUTES (unchanged)
@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (same as before)
    pass

@app.route('/setup', methods=['GET', 'POST'])
def setup_password():
    if request.method == 'POST':
        # ... (same, then advance wizard)
        session['wizard_step'] = 1
        return redirect(url_for('wizard_list'))
    return render_template('setup_password.html')

# WIZARD ROUTES
@app.route('/wizard_list', methods=['GET', 'POST'])
@login_required
def wizard_list():
    if request.method == 'POST':
        session['wizard_step'] = 2
        flash('Great! Now add your first client.')
        return redirect(url_for('wizard_client'))
    return render_template('wizard_list.html')

@app.route('/wizard_client', methods=['GET', 'POST'])
@login_required
def wizard_client():
    if request.method == 'POST':
        session['wizard_step'] = 3
        flash('Welcome complete! Your dashboard awaits.')
        return redirect(url_for('index'))
    return render_template('wizard_client.html')

# SETTINGS (BRANDING #6)
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        org_name = sanitize_input(request.form.get('org_name', 'Your Organization'))
        logo_file = request.files.get('logo')
        if logo_file:
            logo_path = os.path.join('static', 'logo.png')
            logo_file.save(logo_path)
        session['org_name'] = org_name
        with open('static/org_name.txt', 'w') as f:
            f.write(org_name)
        flash('Settings updated!')
        return redirect(url_for('settings'))
    
    org_name = session.get('org_name', open('static/org_name.txt', 'r').read() if os.path.exists('static/org_name.txt') else 'Your Organization')
    return render_template('settings.html', org_name=org_name)

# BACKUP (#4)
@app.route('/backup')
@login_required
def backup_db():
    backup_path = os.path.join(app.config['UPLOAD_FOLDER'], f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    shutil.copy2(app.config['DATABASE'], backup_path)
    return send_file(backup_path, as_attachment=True)

@app.route('/restore', methods=['POST'])
@login_required
def restore_db():
    file = request.files.get('backup_file')
    if file:
        file.save(app.config['DATABASE'])
        flash('Database restored!')
    return redirect(url_for('settings'))

# CLIENTS WITH FUZZY (#2)
@app.route('/check_sanctions/<int:client_id>', methods=['GET'])
@login_required
def check_sanctions(client_id):
    with db.get_cursor() as cursor:
        client = cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,)).fetchone()
        if not client: return jsonify({'error': 'Client not found'}), 404
        
        client_name = client['full_name'].lower()
        sanctions = cursor.execute('SELECT * FROM sanctions_list').fetchall()
        
        matches = []
        for s in sanctions:
            score = fuzz.ratio(client_name, s['full_name'].lower())
            if score > 80:  # Adjustable threshold
                matches.append({'match': dict(s), 'similarity': score})
        
        matches_found = len(matches)
        cursor.execute('UPDATE clients SET risk_score = ? WHERE id = ?', (matches_found, client_id))
        cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                      ('Sanctions Check', client_id, f'Fuzzy match: {matches_found} hits'))
        
        return jsonify({
            'client_id': client_id,
            'matches_found': matches_found,
            'matches': matches
        })

# SANCTIONS IMPORT WITH AUTO-COLUMNS (#3)
@app.route('/sanctions_lists', methods=['GET', 'POST'])
@login_required
def sanctions_lists():
    if request.method == 'POST':
        list_name = sanitize_input(request.form.get('list_name'))
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(file)
            
            # Auto-detect columns
            cols_lower = {col.lower(): col for col in df.columns}
            id_col = next((cols_lower.get(k) for k in ['id', 'ref', 'reference', 'entity_id']), df.columns[0])
            name_col = next((cols_lower.get(k) for k in ['name', 'full_name', 'entity_name', 'individual']), df.columns[1])
            info_col = next((cols_lower.get(k) for k in ['info', 'additional', 'reason', 'comments']), df.columns[2] if len(df.columns) > 2 else None)
            
            with db.get_cursor() as cursor:
                cursor.execute('DELETE FROM sanctions_list WHERE source_list = ?', (list_name,))
                for _, row in df.iterrows():
                    cursor.execute(
                        'INSERT INTO sanctions_list (source_list, original_id, full_name, other_info, list_version_date) VALUES (?, ?, ?, ?, ?)',
                        (list_name, str(row[id_col]), str(row[name_col]), str(row[info_col]) if info_col else '', datetime.now().strftime('%Y-%m-%d'))
                    )
                cursor.execute('INSERT OR REPLACE INTO list_metadata (list_name, last_updated) VALUES (?, CURRENT_TIMESTAMP)', (list_name,))
                cursor.execute('INSERT INTO audit_log (user_action, details) VALUES (?, ?)',
                              ('Sanctions List Updated', f'Imported {len(df)} entries - auto-detected columns'))
            flash(f'✅ {list_name} imported! Auto-detected columns: {id_col}, {name_col}')
        return redirect(url_for('sanctions_lists'))
    
    # ... (rest same as before)
    pass

# REPORT WITH SHA-256 (#1)
@app.route('/reports/<int:client_id>')
@login_required
def generate_report(client_id):
    # ... (same logic until hash)
    
    report_json = json.dumps(report_data, sort_keys=True, indent=2)
    sha256_hash = hashlib.sha256(report_json.encode()).hexdigest()  # REAL SHA-256
    report_data['sha256_hash'] = sha256_hash
    
    # ... (rest same)
    pass

# DASHBOARD, CLIENTS, REPORTS, HELP (same as before, but pass org_name)
@app.route('/')
@login_required
def index():
    org_name = session.get('org_name', 'Your Organization')
    # ... (same queries)
    return render_template('dashboard.html', org_name=org_name, ...)

# All other routes pass org_name=session.get('org_name', 'Your Organization')

if __name__ == '__main__':
    print("Starting MkweliAML v2.0 - Enterprise Edition")
    app.run(debug=False, host='0.0.0.0', port=5000)
