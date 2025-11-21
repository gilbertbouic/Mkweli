# utils.py - Core utilities: manual sanctions parsing, client screening, PDF reports, logging, SHA256
# 100% manual – no downloads. Modular, single responsibility.

import os
import logging
from xml.etree import ElementTree as ET
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from extensions import db
from models import Individual, Alias
from weasyprint import HTML
from jinja2 import Template
from datetime import datetime
from io import BytesIO
import hashlib

logging.basicConfig(level=logging.ERROR)

DATA_DIR = 'data'
LOGS_DIR = 'logs'
os.makedirs(LOGS_DIR, exist_ok=True)

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def update_sanctions_lists():
    """Parse local XML files in data/ – returns dict with record counts for UI."""
    ensure_data_dir()
    files = {
        'un_consolidated.xml': 'UN',
        'uk_consolidated.xml': 'UK',
        'ofac_consolidated.xml': 'OFAC',
        'eu_consolidated.xml': 'EU'
    }
    results = {}
    total_loaded = 0
    for filename in files.keys():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            results[filename] = 0
            continue
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            count = 0
            # Parse individuals
            for elem_list = root.findall('.//INDIVIDUAL') or root.findall('.//INDIVIDUALS/INDIVIDUAL') or []
            for elem in elem_list:
                try:
                    ref = elem.findtext('.//DATAID') or elem.findtext('.//REFERENCE_NUMBER') or 'UNKNOWN'
                    name = elem.findtext('.//FIRST_NAME') + ' ' + elem.findtext('.//LAST_NAME') if elem.findtext('.//FIRST_NAME') else elem.findtext('.//NAME')
                    if not name:
                        continue
                    dob_str = elem.findtext('.//DATE_OF_BIRTH') or elem.findtext('.//DOB') or None
                    nationality = elem.findtext('.//NATIONALITY/VALUE') or elem.findtext('.//NATIONALITY') or None
                    
                    individual = Individual(
                        reference_number=ref.strip(),
                        name=name.strip(),
                        dob=dob_str,
                        nationality=nationality,
                        source=files[filename]
                    )
                    db.session.add(individual)
                    # Aliases
                    alias_elems = elem.findall('.//INDIVIDUAL_ALIAS')
                    for alias_elem in alias_elems:
                        alias_name = alias_elem.findtext('.//ALIAS_NAME')
                        if alias_name:
                            db.session.add(Alias(individual=individual, alias_name=alias_name.strip()))
                    count += 1
                except Exception as e:
                    logging.error(f"Error parsing individual in {filename}: {str(e)}")
            
            # Parse entities (similar structure for most lists)
            entity_list = root.findall('.//ENTITY') or root.findall('.//ENTITIES/ENTITY') or []
            for elem in entity_list:
                try:
                    ref = elem.findtext('.//DATAID') or 'UNKNOWN'
                    name = elem.findtext('.//NAME') or elem.findtext('.//ENTITY_NAME') or 'UNKNOWN'
                    if not name:
                        continue
                    entity = Individual(  # Reuse Individual table for simplicity – or create Entity if needed
                        reference_number=ref.strip(),
                        name=name.strip(),
                        source=files[filename]
                    )
                    db.session.add(entity)
                    count += 1
                except Exception as e:
                    logging.error(f"Error parsing entity in {filename}: {str(e)}")
            
            db.session.commit()
            results[filename] = count
            total_loaded += count
        except Exception as e:
            logging.error(f"Parse error {filename}: {str(e)}")
            results[filename] = 0
    
    return results

def perform_screening(df):
    results = []
    individuals = Individual.query.all()
    if not individuals:
        return results

    for _, row in df.iterrows():
        name = str(row['name']).strip().lower()
        dob = row.get('dob')
        nationality = str(row.get('nationality', '')).strip().lower()

        choices = {ind.id: ind.name.lower() for ind in individuals}
        matches = process.extractBests(name, choices, scorer=fuzz.token_sort_ratio, limit=5)

        for ind_id, score in matches:
            if score < 82:
                continue
            ind = next(i for i in individuals if i.id == ind_id)
            aliases = Alias.query.filter_by(individual_id=ind.id).all()
            alias_list = [a.alias_name for a in aliases] if aliases else []

            results.append({
                'client_name': row['name'],
                'match_name': ind.name,
                'score': score,
                'dob_match': 'Yes' if pd.notna(dob) and str(dob).strip() == str(ind.dob).strip() else 'No',
                'nationality_match': 'Yes' if nationality and nationality == ind.nationality.lower() else 'No',
                'aliases': ', '.join(alias_list) if alias_list else 'None',
                'source': ind.source or 'Unknown',
                'reference': ind.reference_number or 'N/A'
            })
    return results

def generate_pdf_report(results, user_details=None):
    header = ""
    if user_details:
        header = f"""
        <div style="text-align: center; margin-bottom: 30px; color: #561217;">
            <h2>{user_details.get('org_company', 'AML Screening Report')}</h2>
            <p>{user_details.get('address', '')}<br>
            Phone: {user_details.get('phone', '')} | Tax/Reg: {user_details.get('tax_reg', '')}</p>
        </div>
        """

    template_str = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
            h1, h2 {{ color: #561217; }}
            table {{ width: 100%; border-collapse: collapse; margin: 25px 0; }}
            th, td {{ border: 1px solid #561217; padding: 12px; text-align: left; }}
            th {{ background-color: #FBE5B6; color: #561217; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .footer {{ margin-top: 50px; text-align: center; color: #888; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        {header}
        <h1 style="text-align: center; color: #2C6E63;">AML Sanctions Screening Report</h1>
        <p style="text-align: center;">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        {% if results %}
        <table>
            <thead>
                <tr>
                    <th>Client Name</th>
                    <th>Match Name</th>
                    <th>Score</th>
                    <th>DOB Match</th>
                    <th>Nationality Match</th>
                    <th>Aliases</th>
                    <th>Source</th>
                    <th>Reference</th>
                </tr>
            </thead>
            <tbody>
                {% for r in results %}
                <tr>
                    <td>{{ r.client_name }}</td>
                    <td>{{ r.match_name }}</td>
                    <td>{{ r.score }}</td>
                    <td>{{ r.dob_match }}</td>
                    <td>{{ r.nationality_match }}</td>
                    <td>{{ r.aliases }}</td>
                    <td>{{ r.source }}</td>
                    <td>{{ r.reference }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <p style="text-align: center; color: #2C6E63; font-size: 1.2em;">No matches found.</p>
        {% endif %}

        <div class="footer">
            <p>Report generated by AML Shield • Open Source • SHA256: {{ report_hash }}</p>
        </div>
    </body>
    </html>
    """

    # Generate PDF
    template = Template(template_str)
    html_content = template.render(results=results or [], report_hash="TEMP_HASH")  # Placeholder
    html = HTML(string=html_content)
    pdf_buffer = BytesIO()
    html.write_pdf(target=pdf_buffer)
    
    # Calculate real SHA256
    pdf_buffer.seek(0)
    sha256_hash = hashlib.sha256(pdf_buffer.getvalue()).hexdigest()
    
    # Re-render with real hash
    html_content = template.render(results=results or [], report_hash=sha256_hash)
    html = HTML(string=html_content)
    pdf_buffer = BytesIO()
    html.write_pdf(target=pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer, sha256_hash  # Return buffer and hash for logging

    # Logging system - per session, txt file, SHA256 on full file after close
CURRENT_LOG_FILE = None

def start_session_log(user_id, ip):
    global CURRENT_LOG_FILE
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    CURRENT_LOG_FILE = os.path.join(LOGS_DIR, f"session_{user_id}_{timestamp}.txt")
    log_entry(f"Session started | IP: {ip}")

def log_activity(action, details='', report_hash=None):
    if CURRENT_LOG_FILE:
        entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Action: {action} | {details}"
        if report_hash:
            entry += f" | Report SHA256: {report_hash}"
        with open(CURRENT_LOG_FILE, 'a') as f:
            f.write(entry + '\n')

def close_session_log():
    global CURRENT_LOG_FILE
    if CURRENT_LOG_FILE and os.path.exists(CURRENT_LOG_FILE):
        # Calculate SHA256 of full log file
        with open(CURRENT_LOG_FILE, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        with open(CURRENT_LOG_FILE, 'a') as f:
            f.write(f"\n--- SESSION END --- SHA256: {file_hash}\n")
        CURRENT_LOG_FILE = None
