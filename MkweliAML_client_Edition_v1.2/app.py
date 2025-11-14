#!/usr/bin/env python3
"""
MkweliAML - Anti-Money Laundering Compliance System
Production version with ALL improvements
"""

import os
import sys
import re
import hashlib
import json
import shutil
from datetime import datetime
from functools import wraps
from fuzzywuzzy import fuzz

# Note: Removed Levenshtein since fuzzywuzzy has it built-in; simplifies deps

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
    if text is None:
        return ""
    return re.sub(r'[;\"\']', '', str(text)).strip()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize database if not exists
if not os.path.exists(app.config['DATABASE']):
    from init_db import init_database
    init_database()

# Wizard State
WIZARD_STEPS = ['password', 'list', 'client']
if 'wizard_step' not in session:
    session['wizard_step'] = 0

@app.before_request
def check_wizard():
    if not auth_system.is_password_set() and request.endpoint not in ['setup_password', 'static']:
        return redirect(url_for('setup_password'))
    if session['wizard_step'] < len(WIZARD_STEPS) and request.endpoint not in ['static', 'setup_password', 'wizard_list', 'wizard_client', 'login', 'logout']:
        step = WIZARD_STEPS[session['wizard_step']]
        return redirect(url_for(f'wizard_{step}'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if auth_system.verify_password(password):
            session['authenticated'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid password. Please try again.', 'error')
    return render_template('login.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup_password():
    if auth_system.is_password_set():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password == confirm_password and len(password) >= 8:
            auth_system.setup_master_password(password)
            session['authenticated'] = True
            session['wizard_step'] = 1
            flash('Master password set successfully! Now let\'s import a list.', 'success')
            return redirect(url_for('wizard_list'))
        else:
            flash('Passwords do not match or too short (min 8 chars).', 'error')
    return render_template('setup_password.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/wizard_list', methods=['GET', 'POST'])
@login_required
def wizard_list():
    if request.method == 'POST':
        # Handle import (same logic as sanctions_lists POST)
        list_name = sanitize_input(request.form.get('list_name'))
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(file)
            cols_lower = {col.lower(): col for col in df.columns}
            id_col = next((cols_lower.get(k) for k in ['id', 'ref', 'reference', 'entity_id']), df.columns[0] if len(df.columns) > 0 else None)
            name_col = next((cols_lower.get(k) for k in ['name', 'full_name', 'entity_name', 'individual']), df.columns[1] if len(df.columns) > 1 else None)
            info_col = next((cols_lower.get(k) for k in ['info', 'additional', 'reason', 'comments']), df.columns[2] if len(df.columns) > 2 else None)
            
            if id_col and name_col:
                with db.get_cursor() as cursor:
                    cursor.execute('DELETE FROM sanctions_list WHERE source_list = ?', (list_name,))
                    for _, row in df.iterrows():
                        cursor.execute(
                            'INSERT INTO sanctions_list (source_list, original_id, full_name, other_info, list_version_date) VALUES (?, ?, ?, ?, ?)',
                            (list_name, str(row[id_col]), str(row[name_col]), str(row.get(info_col, '')) if info_col else '', datetime.now().strftime('%Y-%m-%d'))
                        )
                    cursor.execute(
                        'INSERT OR REPLACE INTO list_metadata (list_name, last_updated) VALUES (?, CURRENT_TIMESTAMP)',
                        (list_name,)
                    )
                    cursor.execute('INSERT INTO audit_log (user_action, details) VALUES (?, ?)',
                                  ('Sanctions List Updated', f'Wizard: Imported {len(df)} entries for {list_name}'))
                flash(f'List imported! Now add a client.', 'success')
                session['wizard_step'] = 2
                return redirect(url_for('wizard_client'))
            else:
                flash('CSV format error - needs ID and Name columns.', 'error')
        else:
            flash('Upload a CSV file.', 'error')
    
    return render_template('wizard_list.html')

@app.route('/wizard_client', methods=['GET', 'POST'])
@login_required
def wizard_client():
    if request.method == 'POST':
        full_name = sanitize_input(request.form.get('full_name'))
        id_number = sanitize_input(request.form.get('id_number'))
        date_of_birth = sanitize_input(request.form.get('date_of_birth'))
        address = sanitize_input(request.form.get('address'))
        
        if full_name:
            with db.get_cursor() as cursor:
                cursor.execute(
                    'INSERT INTO clients (full_name, id_number, date_of_birth, address) VALUES (?, ?, ?, ?)',
                    (full_name, id_number, date_of_birth, address)
                )
                client_id = cursor.lastrowid
                cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                              ('Client Added', client_id, f'Wizard: Added first client {full_name}'))
            flash('Client added! Setup complete.', 'success')
            session['wizard_step'] = 3
            return redirect(url_for('index'))
        else:
            flash('Full name required.', 'error')
    
    return render_template('wizard_client.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        org_name = sanitize_input(request.form.get('org_name'))
        logo = request.files.get('logo')
        if org_name:
            with open(os.path.join('static', 'org_name.txt'), 'w') as f:
                f.write(org_name)
            session['org_name'] = org_name
        if logo and logo.filename.endswith('.png'):
            logo.save(os.path.join('static', 'logo.png'))
            flash('Logo updated!', 'success')
        flash('Settings saved!', 'success')
        return redirect(url_for('settings'))
    
    org_name = ''
    if os.path.exists(os.path.join('static', 'org_name.txt')):
        with open(os.path.join('static', 'org_name.txt'), 'r') as f:
            org_name = f.read().strip()
    return render_template('settings.html', org_name=org_name)

@app.route('/backup_db')
@login_required
def backup_db():
    backup_path = os.path.join(app.config['UPLOAD_FOLDER'], 'mkweli_backup.db')
    shutil.copy(app.config['DATABASE'], backup_path)
    return send_file(backup_path, as_attachment=True, download_name='mkweli_backup.db')

@app.route('/restore_db', methods=['POST'])
@login_required
def restore_db():
    file = request.files.get('backup_file')
    if file and file.filename.endswith('.db'):
        file.save(app.config['DATABASE'])
        flash('Database restored! Restart the app.', 'success')
    else:
        flash('Upload a .db file.', 'error')
    return redirect(url_for('settings'))

@app.route('/')
@login_required
def index():
    org_name = session.get('org_name', 'MkweliAML')
    with db.get_cursor() as cursor:
        total_clients = cursor.execute('SELECT COUNT(*) FROM clients').fetchone()[0]
        flagged_cases = cursor.execute('SELECT COUNT(*) FROM clients WHERE risk_score > 0').fetchone()[0]
        recent_logs = cursor.execute('SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10').fetchall()
        list_status = cursor.execute('SELECT list_name, last_updated FROM list_metadata').fetchall()
    
    return render_template('dashboard.html', org_name=org_name, total_clients=total_clients, flagged_cases=flagged_cases, recent_logs=recent_logs, list_status=list_status)

@app.route('/clients', methods=['GET', 'POST'])
@login_required
def clients():
    org_name = session.get('org_name', 'MkweliAML')
    if request.method == 'POST':
        full_name = sanitize_input(request.form.get('full_name'))
        id_number = sanitize_input(request.form.get('id_number'))
        date_of_birth = sanitize_input(request.form.get('date_of_birth'))
        address = sanitize_input(request.form.get('address'))
        
        with db.get_cursor() as cursor:
            cursor.execute(
                'INSERT INTO clients (full_name, id_number, date_of_birth, address) VALUES (?, ?, ?, ?)',
                (full_name, id_number, date_of_birth, address)
            )
            client_id = cursor.lastrowid
            cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                          ('Client Added', client_id, f'Added client: {full_name}'))
        
        flash('Client added successfully!', 'success')
        return redirect(url_for('clients'))
    
    with db.get_cursor() as cursor:
        clients_list = cursor.execute('SELECT * FROM clients ORDER BY created_at DESC').fetchall()
    
    return render_template('clients.html', org_name=org_name, clients=clients_list)

@app.route('/clients/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    with db.get_cursor() as cursor:
        client = cursor.execute('SELECT full_name FROM clients WHERE id = ?', (client_id,)).fetchone()
        if client:
            cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))
            cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                          ('Client Deleted', client_id, f'Deleted client: {client["full_name"]}'))
            flash('Client deleted successfully!', 'success')
        else:
            flash('Client not found.', 'error')
    return redirect(url_for('clients'))

@app.route('/check_sanctions/<int:client_id>', methods=['GET'])
@login_required
def check_sanctions(client_id):
    with db.get_cursor() as cursor:
        client = cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,)).fetchone()
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        client_name = client['full_name'].lower()
        sanctions_matches = cursor.execute('''
            SELECT * FROM sanctions_list 
            WHERE LOWER(full_name) LIKE ? 
            OR LOWER(full_name) LIKE ?
            OR LOWER(full_name) LIKE ?
        ''', (
            f'%{client_name}%',
            f'%{client_name.split()[0]}%' if ' ' in client_name else '',
            f'%{client_name.split()[-1]}%' if ' ' in client_name else ''
        )).fetchall()
        
        matches = []
        for match in sanctions_matches:
            similarity = fuzz.token_sort_ratio(client_name, match['full_name'].lower())
            if similarity > 80:  # Threshold for fuzzy match
                matches.append(dict(match))
        
        matches_found = len(matches)
        cursor.execute('UPDATE clients SET risk_score = ? WHERE id = ?', (matches_found, client_id))
        cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                      ('Sanctions Check', client_id, f'Found {matches_found} fuzzy matches for {client["full_name"]}'))
    
    return jsonify({
        'client_id': client_id,
        'matches_found': matches_found,
        'matches': matches
    })

@app.route('/sanctions_lists', methods=['GET', 'POST'])
@login_required
def sanctions_lists():
    org_name = session.get('org_name', 'MkweliAML')
    if request.method == 'POST':
        list_name = sanitize_input(request.form.get('list_name'))
        file = request.files.get('file')
        
        if file and file.filename.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(file)
            cols_lower = {col.lower(): col for col in df.columns}
            id_col = next((cols_lower.get(k) for k in ['id', 'ref', 'reference', 'entity_id']), None)
            name_col = next((cols_lower.get(k) for k in ['name', 'full_name', 'entity_name', 'individual']), None)
            info_col = next((cols_lower.get(k) for k in ['info', 'additional', 'reason', 'comments']), None)
            
            if not id_col or not name_col:
                flash('CSV must have ID and Name columns (auto-detect failed).', 'error')
                return redirect(url_for('sanctions_lists'))
            
            with db.get_cursor() as cursor:
                cursor.execute('DELETE FROM sanctions_list WHERE source_list = ?', (list_name,))
                for _, row in df.iterrows():
                    cursor.execute(
                        'INSERT INTO sanctions_list (source_list, original_id, full_name, other_info, list_version_date) VALUES (?, ?, ?, ?, ?)',
                        (list_name, str(row[id_col]), str(row[name_col]), str(row.get(info_col, '')) if info_col else '', datetime.now().strftime('%Y-%m-%d'))
                    )
                cursor.execute(
                    'INSERT OR REPLACE INTO list_metadata (list_name, last_updated) VALUES (?, CURRENT_TIMESTAMP)',
                    (list_name,)
                )
                cursor.execute('INSERT INTO audit_log (user_action, details) VALUES (?, ?)',
                              ('Sanctions List Updated', f'Updated {list_name} with {len(df)} entries (auto-columns: {id_col}, {name_col})'))
            flash(f'{list_name} sanctions list imported successfully! {len(df)} entries added.', 'success')
        else:
            flash('Please upload a valid CSV file.', 'error')
    
    with db.get_cursor() as cursor:
        lists = cursor.execute('SELECT list_name, last_updated FROM list_metadata').fetchall()
        list_counts = {}
        for lst in lists:
            list_counts[lst['list_name']] = cursor.execute(
                'SELECT COUNT(*) FROM sanctions_list WHERE source_list = ?', (lst['list_name'],)
            ).fetchone()[0]
    
    return render_template('sanctions_lists.html', org_name=org_name, lists=lists, list_counts=list_counts)

@app.route('/reports')
@login_required
def reports():
    org_name = session.get('org_name', 'MkweliAML')
    with db.get_cursor() as cursor:
        clients = cursor.execute('SELECT * FROM clients ORDER BY created_at DESC').fetchall()
        list_status = cursor.execute('SELECT list_name, last_updated FROM list_metadata').fetchall()
        audit_logs = cursor.execute(
            'SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 50'
        ).fetchall()
    
    return render_template('reports.html', org_name=org_name, clients=clients, list_status=list_status, audit_logs=audit_logs)

@app.route('/reports/<int:client_id>')
@login_required
def generate_report(client_id):
    org_name = session.get('org_name', 'MkweliAML')
    try:
        with db.get_cursor() as cursor:
            client = cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,)).fetchone()
            if not client:
                flash('Client not found.', 'error')
                return redirect(url_for('reports'))
            
            list_status = cursor.execute('SELECT list_name, last_updated FROM list_metadata').fetchall()
            
            client_name = client['full_name'].lower()
            sanctions_matches = cursor.execute('''
                SELECT * FROM sanctions_list 
                WHERE LOWER(full_name) LIKE ? 
                OR LOWER(full_name) LIKE ?
                OR LOWER(full_name) LIKE ?
            ''', (
                f'%{client_name}%',
                f'%{client_name.split()[0]}%' if ' ' in client_name else '',
                f'%{client_name.split()[-1]}%' if ' ' in client_name else ''
            )).fetchall()
            
            report_data = {
                'report_id': f"MKW-{client_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                'client_info': dict(client),
                'screening_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'sanctions_lists_used': [dict(lst) for lst in list_status],
                'matches_found': len(sanctions_matches),
                'matches': [dict(match) for match in sanctions_matches],
                'risk_assessment': 'HIGH RISK' if len(sanctions_matches) > 0 else 'LOW RISK',
                'risk_level': 'danger' if len(sanctions_matches) > 0 else 'success'
            }
            
            report_json = json.dumps(report_data, sort_keys=True, indent=2)
            sha_hash = hashlib.sha256(report_json.encode()).hexdigest()
            report_data['sha256_hash'] = sha_hash
            
            cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                          ('Report Generated', client_id, f'Generated report with hash: {sha_hash[:16]}...'))
        
        if WEASYPRINT_AVAILABLE:
            pdf_html = render_template('pdf_report.html', report=report_data, org_name=org_name)
            pdf_file = HTML(string=pdf_html).write_pdf()
            response = make_response(pdf_file)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=MkweliAML_Report_{client_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
            return response
        else:
            return render_template('report_template.html', report=report_data, org_name=org_name)
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/help')
@login_required
def help():
    org_name = session.get('org_name', 'MkweliAML')
    return render_template('help.html', org_name=org_name)

@app.route('/clear_all_clients')
@login_required
def clear_all_clients():
    with db.get_cursor() as cursor:
        client_count = cursor.execute('SELECT COUNT(*) FROM clients').fetchone()[0]
        cursor.execute('DELETE FROM clients')
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="clients"')
        cursor.execute('INSERT INTO audit_log (user_action, details) VALUES (?, ?)',
                      ('System Action', f'All {client_count} clients deleted by user'))
    flash(f'All {client_count} clients have been deleted successfully!', 'success')
    return redirect(url_for('clients'))

@app.route('/clear_all_activity')
@login_required
def clear_all_activity():
    with db.get_cursor() as cursor:
        cursor.execute('DELETE FROM audit_log')
        cursor.execute('INSERT INTO audit_log (user_action, details) VALUES (?, ?)',
                      ('System Action', 'All activity logs cleared by user'))
    flash('All activity logs have been cleared successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("Starting MkweliAML Anti-Money Laundering System...")
    print("System URL: http://localhost:5000")
    if not WEASYPRINT_AVAILABLE:
        print("Note: PDF generation disabled. HTML reports available.")
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
