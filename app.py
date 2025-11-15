#!/usr/bin/env python3
"""
MkweliAML - AML & KYC Sanctions Compliance
Production version with ALL improvements
"""

import os
import sys
import re
import hashlib
import json
import shutil
from datetime import datetime, timedelta
from functools import wraps
from fuzzywuzzy import fuzz
import pandas as pd
import requests

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

def load_xlsx_if_empty():
    xlsx_path = 'database.xlsx'
    if os.path.exists(xlsx_path):
        with db.get_cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM sanctions_list')
            if cursor.fetchone()[0] == 0:
                try:
                    xls = pd.ExcelFile(xlsx_path)
                    imported_count = 0
                    for sheet_name in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                        names = [str(cell).split(':', 1)[-1].strip() if ':' in str(cell) else str(cell).strip() for cell in df.iloc[:, 0] if pd.notna(cell) and str(cell).strip()]
                        for name in names:
                            cursor.execute('''
                                INSERT INTO sanctions_list (source_list, full_name, other_info, list_version_date)
                                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                            ''', (sheet_name.upper(), name, 'From official UK/US/UN lists',))
                        imported_count += len(names)
                        cursor.execute('''
                            INSERT OR REPLACE INTO list_metadata (list_name, last_updated)
                            VALUES (?, CURRENT_TIMESTAMP)
                        ''', (sheet_name.upper(),))
                    print(f'Auto-loaded {imported_count} entries from XLSX')
                    flash('Sanctions data auto-loaded from XLSX!', 'success')
                    session['setup_complete'] = True
                except Exception as e:
                    print(f'Error auto-loading XLSX: {str(e)}')
                    flash(f'Error auto-loading XLSX: {str(e)}', 'error')

load_xlsx_if_empty()

def clear_logs_if_needed():
    with db.get_cursor() as cursor:
        cursor.execute('SELECT value FROM system_metadata WHERE key = "last_log_clear"')
        last_clear = cursor.fetchone()
        if last_clear:
            last_date = datetime.strptime(last_clear['value'], '%Y-%m-%d')
            if datetime.now() - last_date > timedelta(days=30):
                cursor.execute('DELETE FROM audit_log')
                cursor.execute('UPDATE system_metadata SET value = ? WHERE key = "last_log_clear"', (datetime.now().strftime('%Y-%m-%d'),))
                cursor.execute('INSERT INTO audit_log (user_action, details) VALUES (?, ?)', ('Auto Clear', 'Monthly logs cleared'))
        else:
            cursor.execute('INSERT INTO system_metadata (key, value) VALUES ("last_log_clear", ?)', (datetime.now().strftime('%Y-%m-%d'),))
clear_logs_if_needed()

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

@app.before_request
def check_wizard():
    with db.get_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM sanctions_list')
        if cursor.fetchone()[0] > 0:
            session['setup_complete'] = True
    if session.get('setup_complete'):
        return
    WIZARD_STEPS = ['password', 'list', 'client']
    if 'wizard_step' not in session:
        session['wizard_step'] = 0
    if auth_system.is_password_set() and session['wizard_step'] == 0:
        session['wizard_step'] = 1
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

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/setup_password', methods=['GET', 'POST'])
def setup_password():
    if auth_system.is_password_set():
        return redirect(url_for('login'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password == confirm_password and len(password) >= 8:
            auth_system.setup_master_password(password)
            session['wizard_step'] = 1
            flash('Master password set successfully!', 'success')
            return redirect(url_for('wizard_list'))
        else:
            flash('Passwords do not match or too short (min 8 chars).', 'error')
    return render_template('setup_password.html')

@app.route('/wizard_list', methods=['GET', 'POST'])
def wizard_list():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.xlsx'):
            try:
                xls = pd.ExcelFile(file)
                imported_count = 0
                with db.get_cursor() as cursor:
                    for sheet_name in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                        names = [str(cell).split(':', 1)[-1].strip() if ':' in str(cell) else str(cell).strip() for cell in df.iloc[:, 0] if pd.notna(cell) and str(cell).strip()]
                        for name in names:
                            cursor.execute('''
                                INSERT OR IGNORE INTO sanctions_list 
                                (source_list, full_name, other_info) 
                                VALUES (?, ?, ?)
                            ''', (sheet_name.upper(), name, 'From official UK/US/UN lists'))
                        imported_count += cursor.rowcount
                        cursor.execute('''
                            INSERT OR REPLACE INTO list_metadata (list_name, last_updated) 
                            VALUES (?, CURRENT_TIMESTAMP)
                        ''', (sheet_name.upper(),))
                if imported_count > 0:
                    flash(f'Successfully imported {imported_count} entries from XLSX!', 'success')
                    session['wizard_step'] = 2
                    return redirect(url_for('wizard_client'))
                else:
                    flash('No names extracted. Check XLSX format.', 'error')
            except Exception as e:
                flash(f'Error importing XLSX: {str(e)}', 'error')
        else:
            flash('Please upload a valid .xlsx file.', 'error')
    return render_template('wizard_list.html')

@app.route('/wizard_client', methods=['GET', 'POST'])
def wizard_client():
    if request.method == 'POST':
        full_name = sanitize_input(request.form.get('full_name'))
        id_number = sanitize_input(request.form.get('id_number'))
        date_of_birth = sanitize_input(request.form.get('date_of_birth'))
        address = sanitize_input(request.form.get('address'))
        if full_name:
            with db.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO clients (full_name, id_number, date_of_birth, address)
                    VALUES (?, ?, ?, ?)
                ''', (full_name, id_number, date_of_birth, address))
                client_id = cursor.lastrowid
                cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                              ('Client Added', client_id, 'First client added via wizard'))
            flash('First client added successfully! Setup complete.', 'success')
            session['wizard_step'] = 3
            session['setup_complete'] = True
            return redirect(url_for('index'))
        else:
            flash('Full name is required.', 'error')
    return render_template('wizard_client.html')

@app.route('/')
@login_required
def index():
    org_name = session.get('org_name', 'MkweliAML - Created by Gilbert Clement Bouic')
    with db.get_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM clients')
        total_clients = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM clients WHERE risk_score > 0')
        flagged_cases = cursor.fetchone()[0]
        cursor.execute('SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 5')
        recent_logs = cursor.fetchall()
        cursor.execute('SELECT list_name, last_updated FROM list_metadata')
        list_status = cursor.fetchall()
    return render_template('dashboard.html', org_name=org_name, total_clients=total_clients, flagged_cases=flagged_cases, recent_logs=recent_logs, list_status=list_status)

@app.route('/clients', methods=['GET', 'POST'])
@login_required
def clients():
    org_name = session.get('org_name', 'MkweliAML - Created by Gilbert Clement Bouic')
    if request.method == 'POST':
        full_name = sanitize_input(request.form.get('full_name'))
        id_number = sanitize_input(request.form.get('id_number'))
        date_of_birth = sanitize_input(request.form.get('date_of_birth'))
        address = sanitize_input(request.form.get('address'))
        if full_name:
            with db.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO clients (full_name, id_number, date_of_birth, address)
                    VALUES (?, ?, ?, ?)
                ''', (full_name, id_number, date_of_birth, address))
                client_id = cursor.lastrowid
                cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                              ('Client Added', client_id, f'Added client: {full_name}'))
            flash('Client added successfully!', 'success')
        else:
            flash('Full name is required.', 'error')
    with db.get_cursor() as cursor:
        cursor.execute('SELECT * FROM clients ORDER BY created_at DESC')
        clients = cursor.fetchall()
    return render_template('clients.html', clients=clients, org_name=org_name)

@app.route('/delete_client/<int:client_id>')
@login_required
def delete_client(client_id):
    with db.get_cursor() as cursor:
        cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                      ('Client Deleted', client_id, f'Deleted client ID: {client_id}'))
    flash('Client deleted successfully!', 'success')
    return redirect(url_for('clients'))

@app.route('/sanctions_lists', methods=['GET', 'POST'])
@login_required
def sanctions_lists():
    org_name = session.get('org_name', 'MkweliAML - Created by Gilbert Clement Bouic')
    with db.get_cursor() as cursor:
        cursor.execute('SELECT list_name, last_updated FROM list_metadata ORDER BY list_name')
        lists = cursor.fetchall()
    return render_template('sanctions_lists.html', lists=lists, org_name=org_name)

@app.route('/update_db', methods=['POST'])
@login_required
def update_db():
    xlsx_path = 'database.xlsx'
    if os.path.exists(xlsx_path):
        try:
            xls = pd.ExcelFile(xlsx_path)
            imported_count = 0
            with db.get_cursor() as cursor:
                cursor.execute('DELETE FROM sanctions_list')
                cursor.execute('DELETE FROM list_metadata')
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                    names = [str(cell).split(':', 1)[-1].strip() if ':' in str(cell) else str(cell).strip() for cell in df.iloc[:, 0] if pd.notna(cell) and str(cell).strip()]
                    for name in names:
                        cursor.execute('''
                            INSERT INTO sanctions_list (source_list, full_name, other_info, list_version_date)
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (sheet_name.upper(), name, 'From official UK/US/UN lists',))
                    imported_count += len(names)
                    cursor.execute('''
                        INSERT OR REPLACE INTO list_metadata (list_name, last_updated)
                        VALUES (?, CURRENT_TIMESTAMP)
                    ''', (sheet_name.upper(),))
            flash(f'Database updated with {imported_count} entries from XLSX!', 'success')
            cursor.execute('INSERT INTO audit_log (user_action, details) VALUES (?, ?)',
                          ('DB Update', f'Updated sanctions from XLSX'))
        except Exception as e:
            flash(f'Error updating DB: {str(e)}', 'error')
    else:
        flash('database.xlsx not found. Place it in root for updates.', 'error')
    return redirect(url_for('sanctions_lists'))

@app.route('/fetch_update', methods=['POST'])
@login_required
def fetch_update():
    gh_url = 'https://raw.githubusercontent.com/gilbertbouic/MkweliAML/main/database.xlsx'
    xlsx_path = 'database.xlsx'
    try:
        response = requests.get(gh_url, timeout=30)
        if response.status_code == 200:
            with open(xlsx_path, 'wb') as f:
                f.write(response.content)
            flash('Fetched latest from GitHub!', 'success')
            # Update DB
            imported_count = 0
            xls = pd.ExcelFile(xlsx_path)
            with db.get_cursor() as cursor:
                cursor.execute('DELETE FROM sanctions_list')
                cursor.execute('DELETE FROM list_metadata')
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                    names = [str(cell).split(':', 1)[-1].strip() if ':' in str(cell) else str(cell).strip() for cell in df.iloc[:, 0] if pd.notna(cell) and str(cell).strip()]
                    for name in names:
                        cursor.execute('''
                            INSERT INTO sanctions_list (source_list, full_name, other_info, list_version_date)
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (sheet_name.upper(), name, 'From official UK/US/UN lists (GitHub update)',))
                    imported_count += len(names)
                    cursor.execute('''
                        INSERT OR REPLACE INTO list_metadata (list_name, last_updated)
                        VALUES (?, CURRENT_TIMESTAMP)
                    ''', (sheet_name.upper(),))
            flash(f'Updated DB with {imported_count} entries!', 'success')
            cursor.execute('INSERT INTO audit_log (user_action, details) VALUES (?, ?)',
                          ('GH Update', 'Fetched and loaded from GitHub'))
        else:
            flash(f'Fetch failed (code {response.status_code}).', 'error')
    except Exception as e:
        flash(f'Error fetching: {str(e)}.', 'error')
    return redirect(url_for('sanctions_lists'))

@app.route('/reports')
@login_required
def reports():
    org_name = session.get('org_name', 'MkweliAML - Created by Gilbert Clement Bouic')
    with db.get_cursor() as cursor:
        cursor.execute('SELECT * FROM clients ORDER BY created_at DESC')
        clients = cursor.fetchall()
    return render_template('reports.html', clients=clients, org_name=org_name)

@app.route('/generate_report/<int:client_id>')
@login_required
def generate_report(client_id):
    org_name = session.get('org_name', 'MkweliAML - Created by Gilbert Clement Bouic')
    try:
        with db.get_cursor() as cursor:
            cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
            client = cursor.fetchone()
            if not client:
                flash('Client not found.', 'error')
                return redirect(url_for('reports'))
            
            cursor.execute('SELECT list_name, last_updated FROM list_metadata')
            lists_used = cursor.fetchall()
            
            cursor.execute('SELECT * FROM sanctions_list')
            sanctions = cursor.fetchall()
            
            matches = [match for match in sanctions if fuzz.token_sort_ratio(client['full_name'], match['full_name']) > 80]
            
            report_data = {
                'report_id': hashlib.sha256(f'{client_id}{datetime.now()}'.encode()).hexdigest()[:16],
                'screening_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'client_info': dict(client),
                'matches_found': len(matches),
                'matches': [dict(match) for match in matches],
                'risk_assessment': 'HIGH RISK' if len(matches) > 0 else 'LOW RISK',
                'risk_level': 'danger' if len(matches) > 0 else 'success',
                'sanctions_lists_used': [dict(lst) for lst in lists_used],
                'sources': 'UK/US/UN official lists'
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
    org_name = session.get('org_name', 'MkweliAML - Created by Gilbert Clement Bouic')
    return render_template('help.html', org_name=org_name)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        org_name = sanitize_input(request.form.get('org_name'))
        if org_name:
            session['org_name'] = org_name
            flash('Organization name updated successfully!', 'success')
        else:
            flash('Please enter a valid organization name.', 'error')
    org_name = session.get('org_name', 'MkweliAML - Created by Gilbert Clement Bouic')
    return render_template('settings.html', org_name=org_name)

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
    print("Starting MkweliAML AML & KYC Sanctions Compliance")
    print("System URL: http://localhost:5000")
    if not WEASYPRINT_AVAILABLE:
        print("Note: PDF generation disabled. HTML reports available.")
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
