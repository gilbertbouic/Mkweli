# utils.py - Handles sanctions data with error handling/performance (loads from local files only).
import os
import logging
from xml.etree import ElementTree as ET
import hashlib
from datetime import datetime
from fuzzywuzzy import fuzz
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from flask import request

from extensions import db
from models import Individual, Entity, Alias, Address, Sanction, Log

logging.basicConfig(level=logging.ERROR)

DATA_DIR = 'data'

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def parse_xml(filepath, source):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        entries = []
        if source == 'un':
            for typ in ['INDIVIDUALS', 'ENTITIES']:
                section = root.find(typ)
                if section is None:
                    continue
                for entry in section.findall(typ[:-1]):
                    name_parts = [entry.findtext(tag) for tag in ['FIRST_NAME', 'SECOND_NAME', 'THIRD_NAME', 'FOURTH_NAME'] if entry.findtext(tag)]
                    name = ' '.join(filter(None, name_parts)).strip()
                    if not name:
                        continue  # Validate required
                    ref = entry.findtext('REFERENCE_NUMBER')
                    dob_str = entry.find('./DATE_OF_BIRTH/DATE').text if entry.find('./DATE_OF_BIRTH/DATE') is not None else None
                    nationality = entry.findtext('NATIONALITY/VALUE')
                    listed_on_str = entry.findtext('LISTED_ON')
                    aliases = [al.findtext('ALIAS_NAME') for al in entry.findall('ALIAS') if al.findtext('ALIAS_NAME')]
                    addresses = [(addr.findtext('STREET'), addr.findtext('CITY'), addr.findtext('COUNTRY')) for addr in entry.findall('ADDRESS')]
                    description = entry.findtext('COMMENTS1')
                    entries.append({
                        'type': 'individual' if typ == 'INDIVIDUALS' else 'entity',
                        'ref': ref, 'name': name, 'dob': dob_str, 'nationality': nationality,
                        'listed_on': listed_on_str, 'aliases': aliases, 'addresses': addresses,
                        'description': description
                    })
        elif source in ['uk', 'eu']:
            for entry in root.findall('.//SanctionsEntry') or root.findall('.//designation'):  # Adapt for UK/EU variations
                name = entry.findtext('Name6') or entry.findtext('fullName') or entry.findtext('wholeName')
                name = name.strip() if name else ''
                if not name:
                    continue
                ref = entry.findtext('uniqueId') or entry.findtext('FileID')
                dob_str = entry.findtext('dateOfBirth') or entry.findtext('birthdate')
                nationality = entry.findtext('nationality') or entry.findtext('citizenship')
                listed_on_str = entry.findtext('listingDate')
                aliases = [al.text for al in entry.findall('.//alias') if al.text]
                addresses = [(addr.findtext('street'), addr.findtext('city'), addr.findtext('country')) for addr in entry.findall('.//address')]
                description = entry.findtext('remarks') or entry.findtext('otherInformation')
                entries.append({
                    'type': 'mixed', 'ref': ref, 'name': name, 'dob': dob_str, 'nationality': nationality,
                    'listed_on': listed_on_str, 'aliases': aliases, 'addresses': addresses,
                    'description': description
                })
        elif source == 'ofac':
            for entry in root.findall('.//sdnEntry'):
                name = entry.findtext('lastName') or ''
                first = entry.findtext('firstName') or ''
                name = f"{first} {name}".strip() if first or name else ''
                if not name:
                    continue
                ref = entry.findtext('uid')
                dob_str = entry.find('./programList/program').text if entry.find('./programList/program') else None  # Adapt; OFAC has no DOB often
                nationality = None  # OFAC often lacks; adapt
                listed_on_str = None
                aliases = [aka.findtext('akaName') for aka in entry.findall('.//akaList/aka') if aka.findtext('akaName')]
                addresses = [(addr.findtext('address1'), addr.findtext('city'), addr.findtext('country')) for addr in entry.findall('.//addressList/address')]
                description = '; '.join([prog.text for prog in entry.findall('.//programList/program') if prog.text])
                entries.append({
                    'type': 'mixed', 'ref': ref, 'name': name, 'dob': dob_str, 'nationality': nationality,
                    'listed_on': listed_on_str, 'aliases': aliases, 'addresses': addresses,
                    'description': description
                })
        return entries
    except Exception as e:
        raise ValueError(f"Parse error in {filepath}: {str(e)}")

def update_sanctions_lists():
    ensure_data_dir()
    files = {
        'un_consolidated.xml': 'un',
        'uk_consolidated.xml': 'uk',
        'eu_consolidated.xml': 'eu',
        'ofac_consolidated.xml': 'ofac',
    }
    data = {}
    for filename, source in files.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            raise ValueError(f"Missing sanctions file: {filename}. Please download manually from official sources, rename as specified, and place in {DATA_DIR}/ folder.")
        data[filename] = parse_xml(filepath, source)
    return data

def incorporate_to_db(parsed_data):
    try:
        with db.session.begin():
            for filename, entries in parsed_data.items():
                source = files[filename]  # From above dict
                for entry in entries:
                    ref = entry.get('ref', '').strip()
                    name = entry.get('name', '').strip()
                    if not ref or not name or len(ref) > 50 or len(name) > 255:
                        continue  # Validate
                    dob = None
                    if entry.get('dob'):
                        try:
                            dob = datetime.strptime(entry['dob'], '%Y-%m-%d').date()  # Adapt formats as needed
                        except ValueError:
                            try:
                                dob = datetime.strptime(entry['dob'], '%d/%m/%Y').date()  # Common variations
                            except ValueError:
                                pass
                    listed_on = None
                    if entry.get('listed_on'):
                        try:
                            listed_on = datetime.strptime(entry['listed_on'], '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    if entry['type'] in ['individual', 'mixed']:
                        ind = Individual(reference_number=ref, name=name, dob=dob,
                                         nationality=entry.get('nationality', '').strip()[:100],
                                         listed_on=listed_on, source=source)
                        db.session.add(ind)
                        db.session.flush()
                        for alias_name in entry.get('aliases', []):
                            alias_name = alias_name.strip()[:255]
                            if alias_name:
                                db.session.add(Alias(individual_id=ind.id, alias_name=alias_name))
                        for addr in entry.get('addresses', []):
                            address_str = ', '.join(filter(None, [a.strip() if a else '' for a in addr]))[:255]
                            country = addr[2].strip()[:100] if len(addr) > 2 else ''
                            if address_str:
                                db.session.add(Address(individual_id=ind.id, address=address_str, country=country))
                        if entry.get('description'):
                            desc = entry['description'].strip()[:5000]  # Limit text
                            db.session.add(Sanction(individual_id=ind.id, description=desc))
                    # Add Entity handling if entry['type'] == 'entity' (similar)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"DB insert error: {str(e)}")

# Other functions unchanged (perform_screening, generate_pdf_report, log_activity)
def perform_screening(client_data):
    try:
        name = client_data.get('name', '').strip().lower()
        dob = client_data.get('dob')
        nationality = client_data.get('nationality', '').strip().lower()
        if not name:
            raise ValueError("Client name required for screening.")
        matches = []
        candidates = Individual.query.filter(Individual.name.ilike(f'%{name}%')).all()
        for cand in candidates:
            name_score = fuzz.token_sort_ratio(name, cand.name.lower())
            score = name_score
            if dob and cand.dob:
                dob_score = 100 if cand.dob == dob else 0
                score = (score + dob_score) / 2
            if nationality and cand.nationality:
                nat_score = fuzz.ratio(nationality, cand.nationality.lower())
                score = (score + nat_score) / 2 if len([score, nat_score]) > 1 else score
            if score >= 82:
                matches.append({'id': cand.id, 'name': cand.name, 'score': score})
        return matches
    except Exception as e:
        logging.error(f"Screening error: {str(e)}")
        raise ValueError(f"Screening failed: {str(e)}")

def generate_pdf_report(report_data):
    try:
        if not report_data:
            raise ValueError("Report data required.")
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html')
        html = template.render(report_data=report_data)
        pdf_bytes = HTML(string=html).write_pdf()
        report_hash = hashlib.sha256(pdf_bytes).hexdigest()
        return pdf_bytes, report_hash
    except Exception as e:
        logging.error(f"PDF generation error: {str(e)}")
        raise ValueError(f"Failed to generate report: {str(e)}")

def log_activity(user_id, action, report_hash=None):
    try:
        if not user_id or not action:
            raise ValueError("User ID and action required.")
        ip = request.remote_addr if request else 'unknown'
        log = Log(user_id=user_id, action=action.strip(), ip=ip, report_hash=report_hash)
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(f"Logging error: {str(e)}")
        raise ValueError(f"Failed to log: {str(e)}")
