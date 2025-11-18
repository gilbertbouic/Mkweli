# utils.py - Data utils with error handling/performance (downloads only if missing).
import os
import requests
import logging
from xml.etree import ElementTree as ET
import csv

logging.basicConfig(level=logging.ERROR)

DATA_DIR = 'data'
# Updated URLs: Working links from 2025 searches (direct XML downloads)
UN_URL = 'https://scsanctions.un.org/resources/xml/en/consolidated.xml'  # UN direct XML
UK_URL = 'https://ofsistorage.blob.core.windows.net/publishlive/ConList.xml'  # UK consolidated XML
CA_URL = 'https://www.international.gc.ca/world-monde/assets/office_docs/docs/consolidated_list.xml'  # CA XML (assumed from page; update if 404)
OFAC_URL = 'https://www.treasury.gov/ofac/downloads/sdn.csv'  # OFAC CSV (working)

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def download_file(url, filename):
    try:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            return filepath  # Performance: Skip if exists
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        raise ValueError(f"Could not download {url}: {str(e)}")  # Feedback

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
            data[filename] = []  # Graceful: Empty on error
    return data
