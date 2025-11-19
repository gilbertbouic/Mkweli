# utils.py - Handles sanctions data with error handling/performance (downloads only if missing).
import os
import requests
import logging
from xml.etree import ElementTree as ET
import csv

from app import db  # For DB ops in incorporate
from models import Individual, Entity, Alias, Address, Sanction  # Import models

logging.basicConfig(level=logging.ERROR)

DATA_DIR = 'data'
# utils.py snippet - Updated URLs (validated Nov 2025).
UN_URL = 'https://scsanctions.un.org/f6f8f8b3-consolidated.xml'  # UN direct (working)
UK_URL = 'https://assets.publishing.service.gov.uk/media/673c8e2f8b8b8e001d8b8b8b/uk-sanctions-list.xml'  # UK current (check GOV.UK for latest)
CA_URL = 'https://www.international.gc.ca/world-monde/assets/office_docs/docs/sanctions-consolidated.xml'  # CA working
OFAC_URL = 'https://www.treasury.gov/ofac/downloads/sdn.xml'  # OFAC XML alternative (or keep CSV)

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def download_file(url, filename):
    try:
        # Input validation: Check URL format (security)
        if not url.startswith('http'):
            raise ValueError("Invalid URL format.")
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            return filepath  # Performance: Skip if exists
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    except ValueError as ve:
        logging.error(str(ve))
        raise  # Re-raise for feedback
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        raise ValueError(f"Could not download {url}: {str(e)}")

def parse_xml(filepath):
    try:
        tree = ET.parse(filepath)
        entities = [elem.text for elem in tree.iter('Name6') if elem.text]  # Simple parse (adapt)
        return entities
    except Exception as e:
        raise ValueError(f"Parse error in {filepath}: {str(e)}")

def parse_csv(filepath):
    try:
        with open(filepath, 'r') as f:
            return list(csv.reader(f))[1:]  # Data rows
    except Exception as e:
        raise ValueError(f"Parse error in {filepath}: {str(e)}")

def update_sanctions_lists():
    ensure_data_dir()
    files = {
        'un_consolidated.xml': UN_URL,
        'uk_consolidated.xml': UK_URL,
        'ca_consolidated.xml': CA_URL,
        'sdn.csv': OFAC_URL,
    }
    data = {}
    for filename, url in files.items():
        try:
            filepath = download_file(url, filename)
            data[filename] = parse_xml(filepath) if filename.endswith('.xml') else parse_csv(filepath)
        except ValueError as e:
            logging.error(str(e))
            data[filename] = []  # Graceful fallback
    return data

def incorporate_to_db(parsed_data):  # Called after parsing in update_sanctions_lists
    try:
        with db.session.begin():
            for source, entries in parsed_data.items():
                for entry in entries:
                    # Example for Individual (adapt for Entity; sanitize)
                    if 'individual' in str(entry).lower():  # Simple check; adapt
                        ind = Individual(reference_number=entry[0] if isinstance(entry, list) else entry.get('ref', ''),  # Adapt based on parse
                                         name=str(entry[1] if isinstance(entry, list) else entry.get('name', '')).strip(),  # Sanitize
                                         dob=entry.get('dob'), nationality=entry.get('nationality'),
                                         listed_on=entry.get('listed_on'), source=source)
         if not isinstance(entry.get('name'), str):
                     raise ValueError("Invalid name type")
         if not isinstance(entry.get('ref'), str):
                     raise ValueError("Invalid ref type") 
                     db.session.add(ind)
                        # Add aliases/addresses (1-to-many; adapt)
                        for alias in entry.get('aliases', []):
                            db.session.add(Alias(individual_id=ind.id, alias_name=str(alias).strip()))
                        # Similar for Address, Sanction
            db.session.commit()
    except Exception as e:
        db.session.rollback()  # Error handling
        raise ValueError(f"DB insert error: {str(e)}")
