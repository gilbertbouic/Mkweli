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
import logging
from datetime import datetime, timedelta
from functools import wraps
from fuzzywuzzy import fuzz
import pandas as pd
import requests
import csv
import xml.etree.ElementTree as ET
from io import StringIO, BytesIO

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
os.makedirs('logs', exist_ok=True)  # For logging

# Setup logging
logging.basicConfig(filename='logs/app.log', level=logging.ERROR, format='%(asctime)s %(levelname)s: %(message)s')

auth_system = AuthSystem()

def sanitize_input(input_str):
    if input_str is None:
        return None
    return re.sub(r'[^\w\s-]', '', input_str)

# Initialization code here (run once at startup)
with app.app_context():
    with app.test_request_context():
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
                                        INSERT OR IGNORE INTO sanctions_list (source_list, full_name, other_info, list_version_date)
                                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                                    ''', (sheet_name.upper(), name, 'From official UK/US/UN lists',))
                                    if cursor.rowcount > 0:
                                        imported_count += 1
                                cursor.execute('''
                                    INSERT OR REPLACE INTO list_metadata (list_name, last_updated)
                                    VALUES (?, CURRENT_TIMESTAMP)
                                ''', (sheet_name.upper(),))
                            print(f'Auto-loaded {imported_count} unique entries from XLSX')
                            flash('Sanctions data auto-loaded from XLSX!', 'success')
                            session['setup_complete'] = True
                        except Exception as e:
                            logging.error(f'Error auto-loading XLSX: {str(e)}')
                            flash(f'Error auto-loading XLSX: {str(e)}', 'error')

        def clear_logs_if_needed():
            with db.get_cursor() as cursor:
                cursor.execute('SELECT value FROM system_metadata WHERE key = "last_log_clear"')
                last_clear = cursor.fetchone()
                if last_clear:
                    last_date = datetime.strptime(last_clear[0], '%Y-%m-%d')
                    if datetime.now() - last_date > timedelta(days=30):
                        cursor.execute('DELETE FROM audit_log WHERE timestamp < ?', (last_date,))
                        cursor.execute('INSERT OR REPLACE INTO system_metadata (key, value) VALUES (?, ?)',
                                       ('last_log_clear', datetime.now().strftime('%Y-%m-%d')))

        load_xlsx_if_empty()
        clear_logs_if_needed()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def check_password_set():
    if not auth_system.is_password_set() and request.endpoint not in ('setup_password', 'static'):
        return redirect(url_for('setup_password'))

# Use a flag for run-once (since Flask 3.0 deprecates before_first_request; this works in 2.3.3 but future-proof)
fetched_lists = False
@app.before_request
def auto_fetch_if_not_done():
    global fetched_lists
    if not fetched_lists:
        auto_fetch_sanctions_lists()
        fetched_lists = True

def auto_fetch_sanctions_lists():
    sources = {
        'UN': {
            'url': 'https://www.un.org/securitycouncil/sites/www.un.org.securitycouncil/files/consolidated.xml',  # Official UN XML, last Nov 6 2025
            'parser': parse_un_xml
        },
        'OFAC': {
            'url': 'https://www.treasury.gov/ofac/downloads/sdn.csv',  # Official US CSV
            'parser': parse_ofac_csv
        },
        'UK': {
            'url': 'https://assets.publishing.service.gov.uk/media/66f7b2d2f89c2f0d1d2b2b2a/UK_Sanctions_List.ods',  # Latest as of Nov 16 2025; monitor for changes
            'parser': parse_uk_ods
        },
        'EU': {
            'url': 'https://webgate.ec.europa.eu/europeaid/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content',  # Official EU XML
            'parser': parse_eu_xml
        },
        'CANADA': {
            'url': 'https://www.international.gc.ca/world-monde/assets/office_docs/international_relations-relations_internationales/sanctions/consolidated_list.xml',  # Official Canada XML, last Nov 6 2025
            'parser': parse_canada_xml
        }
    }
    for source, info in sources.items():
        try:
            response = requests.get(info['url'], timeout=10)
            response.raise_for_status()
            content_hash = hashlib.sha256(response.content).hexdigest()
            with db.get_cursor() as cursor:
                cursor.execute('SELECT value FROM system_metadata WHERE key = ?', (f'{source}_hash',))
                last_hash = cursor.fetchone()
                if last_hash and last_hash[0] == content_hash:
                    continue  # No change, skip
            if 'xml' in response.headers.get('Content-Type', ''):
                data = response.content
            else:
                data = response.text
            entries = info['parser'](data, source)
            with db.get_cursor() as cursor:
                cursor.execute('DELETE FROM sanctions_list WHERE source_list = ?', (source,))  # Clear old
                existing = set(row[0].lower() for row in cursor.execute('SELECT full_name FROM sanctions_list').fetchall())
                imported = 0
                for entry in entries:
                    name_lower = entry['full_name'].lower()
                    if name_lower not in existing and len(entry['full_name']) > 0:
                        cursor.execute('INSERT INTO sanctions_list (source_list, full_name, other_info, list_version_date) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
                                       (source, entry['full_name'], entry.get('other_info', ''),))
                        imported += 1
                        existing.add(name_lower)
                cursor.execute('INSERT OR REPLACE INTO list_metadata (list_name, last_updated) VALUES (?, CURRENT_TIMESTAMP)', (source,))
                cursor.execute('INSERT OR REPLACE INTO system_metadata (key, value) VALUES (?, ?)', (f'{source}_hash', content_hash))
            logging.info(f'Fetched and imported {imported} new unique entries from {source}')
            flash(f'Updated {source} list with {imported} new entries!', 'success')
        except requests.RequestException as e:
            logging.error(f'Fetch failed for {source}: {str(e)}')
            flash(f'Failed to update {source} list: Network error. Using cached local data.', 'warning')
        except Exception as e:
            logging.error(f'Parse failed for {source}: {str(e)}')
            flash(f'Format change detected for {source} list: {str(e)}. Manual update recommended.', 'error')

# Parser functions (each <50 lines, with error handling)
def parse_un_xml(data, source):
    try:
        root = ET.fromstring(data)
        entries = []
        for indiv in root.findall('.//INDIVIDUAL'):
            first = indiv.find('FIRST_NAME').text or ''
            second = indiv.find('SECOND_NAME').text or ''
            name = f'{first} {second}'.strip()
            if name:
                other_info = indiv.find('COMMENTS1').text or ''
                entries.append({'full_name': name, 'other_info': other_info})
        return entries
    except ET.ParseError as e:
        raise ValueError("Invalid XML format for UN list") from e
    except AttributeError:
        raise ValueError("Unexpected XML structure change in UN list")

def parse_ofac_csv(data, source):
    try:
        reader = csv.reader(StringIO(data))
        entries = []
        header = next(reader, None)
        if not header or 'ent_num' not in header[0]:
            raise ValueError("Missing or changed CSV header in OFAC list")
        for row in reader:
            if row and len(row) > 1:
                name = row[1].strip()
                other_info = row[-1] if len(row) > 11 else ''
                if name:
                    entries.append({'full_name': name, 'other_info': other_info})
        return entries
    except csv.Error as e:
        raise ValueError("Invalid CSV format for OFAC list") from e

def parse_uk_ods(data, source):
    try:
        df = pd.read_excel(BytesIO(data), engine='openpyxl' if data[0:4] == b'PK\x03\x04' else 'odf', sheet_name=0, header=1)  # Detect engine by magic bytes
        entries = []
        for _, row in df.iterrows():
            name_parts = [str(row.get(f'Name {i}', '')) for i in range(1, 7)]
            name = ' '.join(part.strip() for part in name_parts if part and part != 'nan')
            if name:
                other_info = str(row.get('Remarks', '')) or ''
                entries.append({'full_name': name, 'other_info': other_info})
        return entries
    except ValueError as e:
        if 'odf' in str(e) or 'openpyxl' in str(e):
            raise ValueError("Invalid file format for UK list; try different extension") from e
        raise ValueError("Invalid ODS/XLSX structure or tampered columns in UK list") from e
    except Exception as e:
        raise ValueError("Unexpected error in UK ODS parsing") from e

def parse_eu_xml(data, source):
    try:
        root = ET.fromstring(data)
        entries = []
        for entity in root.findall('.//sanctionEntity'):
            name_elem = entity.find('nameAlias')
            name = name_elem.get('wholeName') if name_elem is not None else ''
            if name:
                other_info = entity.find('regulation/regulationSummary').text or ''
                entries.append({'full_name': name.strip(), 'other_info': other_info})
        return entries
    except ET.ParseError as e:
        raise ValueError("Invalid XML format for EU list") from e
    except AttributeError:
        raise ValueError("Unexpected XML structure change in EU list")

def parse_canada_xml(data, source):
    try:
        root = ET.fromstring(data)
        entries = []
        for item in root.findall('.//item'):
            name = item.find('name').text or ''
            if name:
                other_info = item.find('description').text or ''
                entries.append({'full_name': name.strip(), 'other_info': other_info})
        return entries
    except ET.ParseError as e:
        raise ValueError("Invalid XML format for Canada list") from e
    except AttributeError:
        raise ValueError("Unexpected XML structure change in Canada list")

@app.route('/')
@app.route('/index')
@login_required
def index():
    # Fetch dashboard data
    with db.get_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM clients')
        total_clients = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM clients WHERE risk_score > 0')
        flagged_cases = cursor.fetchone()[0]
        cursor.execute('SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10')
        recent_logs = cursor.fetchall()
        cursor.execute('SELECT * FROM list_metadata')
        list_status = cursor.fetchall()
    return render_template('dashboard.html', total_clients=total_clients, flagged_cases=flagged_cases, recent_logs=recent_logs, list_status=list_status)

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

@app.route('/setup_password', methods=['GET', 'POST'])
def setup_password():
    if auth_system.is_password_set():
        return redirect(url_for('login'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if password == confirm and len(password) >= 8:
            auth_system.setup_master_password(password)
            session['authenticated'] = True
            flash('Password set successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Passwords do not match or too short.', 'error')
    return render_template('setup_password.html')

@app.route('/clients', methods=['GET', 'POST'])
@login_required
def clients():
    if request.method == 'POST':
        full_name = sanitize_input(request.form.get('full_name'))
        id_number = sanitize_input(request.form.get('id_number'))
        date_of_birth = sanitize_input(request.form.get('date_of_birth'))
        address = sanitize_input(request.form.get('address'))
        if full_name:
            with db.get_cursor() as cursor:
                cursor.execute('INSERT INTO clients (full_name, id_number, date_of_birth, address) VALUES (?, ?, ?, ?)',
                               (full_name, id_number, date_of_birth, address))
                client_id = cursor.lastrowid
                cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                               ('Client Created', client_id, f'Added client {full_name}'))
            flash('Client added successfully!', 'success')
        else:
            flash('Full name is required.', 'error')
    with db.get_cursor() as cursor:
        cursor.execute('SELECT * FROM clients ORDER BY created_at DESC')
        clients = cursor.fetchall()
    return render_template('clients.html', clients=clients)

@app.route('/delete_client/<int:client_id>', methods=['POST'])
@login_required
def delete_client(client_id):
    with db.get_cursor() as cursor:
        cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                       ('Client Deleted', client_id, f'Deleted client ID {client_id}'))
    flash('Client deleted successfully!', 'success')
    return redirect(url_for('clients'))

@app.route('/check_sanctions/<int:client_id>')
@login_required
def check_sanctions(client_id):
    with db.get_cursor() as cursor:
        cursor.execute('SELECT full_name FROM clients WHERE id = ?', (client_id,))
        client = cursor.fetchone()
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        client_name = client[0]
        cursor.execute('SELECT full_name, source_list, other_info FROM sanctions_list')
        sanctions = cursor.fetchall()
        matches = []
        for s in sanctions:
            if fuzz.ratio(client_name.lower(), s[0].lower()) > 80:
                matches.append({'full_name': s[0], 'source_list': s[1], 'other_info': s[2]})
        risk_score = len(matches)
        cursor.execute('UPDATE clients SET risk_score = ? WHERE id = ?', (risk_score, client_id))
        cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                       ('Sanctions Check', client_id, f'Found {risk_score} matches for {client_name}'))
    return jsonify({'matches_found': risk_score, 'matches': matches, 'client_id': client_id})

@app.route('/sanctions_lists', methods=['GET', 'POST'])
@login_required
def sanctions_lists():
    if request.method == 'POST' and request.form.get('action') == 'refresh':
        auto_fetch_sanctions_lists()
        return redirect(url_for('sanctions_lists'))
    with db.get_cursor() as cursor:
        cursor.execute('SELECT list_name, last_updated, (SELECT COUNT(*) FROM sanctions_list WHERE source_list = list_name) AS count FROM list_metadata')
        lists = cursor.fetchall()
    return render_template('sanctions_lists.html', lists=lists)

@app.route('/import_consolidated', methods=['POST'])
@login_required
def import_consolidated():
    files = request.files.getlist('files')
    imported = 0
    for file in files:
        if file.filename:
            try:
                source = file.filename.split('.')[0].upper()
                data = file.read()
                if file.filename.endswith('.xml'):
                    entries = parse_un_xml(data, source) if 'UN' in source else parse_eu_xml(data, source) if 'EU' in source else parse_canada_xml(data, source) if 'CANADA' in source else []
                elif file.filename.endswith('.csv'):
                    entries = parse_ofac_csv(data.decode('utf-8'), source)
                elif file.filename.endswith(('.ods', '.xlsx')):
                    entries = parse_uk_ods(data, source)
                else:
                    raise ValueError("Unsupported file format")
                with db.get_cursor() as cursor:
                    cursor.execute('DELETE FROM sanctions_list WHERE source_list = ?', (source,))
                    existing = set(row[0].lower() for row in cursor.execute('SELECT full_name FROM sanctions_list').fetchall())
                    for entry in entries:
                        name_lower = entry['full_name'].lower()
                        if name_lower not in existing and len(entry['full_name']) > 0:
                            cursor.execute('INSERT INTO sanctions_list (source_list, full_name, other_info, list_version_date) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
                                           (source, entry['full_name'], entry.get('other_info', ''),))
                            imported += 1
                            existing.add(name_lower)
                    cursor.execute('INSERT OR REPLACE INTO list_metadata (list_name, last_updated) VALUES (?, CURRENT_TIMESTAMP)', (source,))
                file.seek(0)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            except Exception as e:
                logging.error(f'Import failed for {file.filename}: {str(e)}')
                flash(f'Error importing {file.filename}: {str(e)}. Format may have changed.', 'error')
    flash(f'Imported {imported} new unique entries from consolidated lists!', 'success')
    return redirect(url_for('sanctions_lists'))

@app.route('/reports')
@login_required
def reports():
    with db.get_cursor() as cursor:
        cursor.execute('SELECT * FROM clients ORDER BY created_at DESC')
        clients = cursor.fetchall()
        cursor.execute('SELECT * FROM list_metadata')
        list_status = cursor.fetchall()
        cursor.execute('SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 20')
        audit_logs = cursor.fetchall()
    return render_template('reports.html', clients=clients, list_status=list_status, audit_logs=audit_logs)

@app.route('/generate_report/<int:client_id>')
@login_required
def generate_report(client_id):
    try:
        with db.get_cursor() as cursor:
            cursor.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
            client_info = cursor.fetchone()
            if not client_info:
                flash('Client not found', 'error')
                return redirect(url_for('reports'))
            
            cursor.execute('SELECT full_name, source_list, other_info FROM sanctions_list WHERE LOWER(full_name) LIKE ?', (f'%{client_info["full_name"].lower()}%',))
            matches = cursor.fetchall()
            cursor.execute('SELECT list_name, last_updated FROM list_metadata')
            lists_used = cursor.fetchall()
            
            report_data = {
                'report_id': f'R-{client_id}-{datetime.now().strftime("%Y%m%d")}',
                'screening_date': datetime.now().isoformat(),
                'client_info': client_info,
                'risk_assessment': 'Low' if client_info['risk_score'] == 0 else 'High',
                'matches': matches,
                'sanctions_lists_used': lists_used,
                'sha256_hash': hashlib.sha256(json.dumps(client_info).encode()).hexdigest()  # Improved hash
            }
            cursor.execute('INSERT INTO audit_log (user_action, client_id, details) VALUES (?, ?, ?)',
                           ('Report Generated', client_id, f'Generated report with hash: {report_data["sha256_hash"][:16]}...'))
        
        org_name = session.get('org_name', 'MkweliAML')
        
        if WEASYPRINT_AVAILABLE:
            pdf_html = render_template('report_template.html', report=report_data, org_name=org_name)
            pdf_file = HTML(string=pdf_html).write_pdf()
            response = make_response(pdf_file)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=MkweliAML_Report_{client_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
            return response
        else:
            return render_template('report_template.html', report=report_data, org_name=org_name)
    except Exception as e:
        logging.error(f'Error generating report for client {client_id}: {str(e)}')
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
        cursor.execute('SELECT COUNT(*) FROM clients')
        client_count = cursor.fetchone()[0]
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
