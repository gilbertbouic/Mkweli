import csv
import difflib
import io
import json
import os
import pandas as pd
import requests
import unittest
from flask import Flask, flash, jsonify, make_response, redirect, render_template, request, url_for
from lxml import html

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For flash msgs

# Cross-platform data dir
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

SANCTIONS_SOURCES = {
    'UN': {
        'base_url': 'https://www.un.org/securitycouncil/content/un-sc-consolidated-list',
        'xml_path': "//a[contains(@href, 'consolidated.xml')]/@href",
        'file': os.path.join(DATA_DIR, 'un_consolidated.xml'),
        'error_msg': 'Network error on UN: Using cache'
    },
    'UK': {
        'url': 'https://ofsistorage.blob.core.windows.net/publishlive/ConList.xml',
        'file': os.path.join(DATA_DIR, 'uk_consolidated.xml'),
        'error_msg': 'Network error on UK: Using cache'
    },
    'EU': {
        'url': 'https://webgate.ec.europa.eu/europeaid/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw',
        'file': os.path.join(DATA_DIR, 'eu_consolidated.xml'),
        'error_msg': 'Network error on EU: Using cache'
    },
    'US': {
        'url': 'https://www.treasury.gov/ofac/downloads/sdn.xml',
        'file': os.path.join(DATA_DIR, 'us_sdn.xml'),
        'error_msg': 'Network error on US: Using cache'
    },
    'CA': {
        'url': 'https://open.canada.ca/data/en/dataset/82e08a00-9f81-40d0-9b6c-1a805cbc0865/resource/73c2a91d-652f-4af0-a194-f4b34de2eead/download/consolidated.xml',
        'file': os.path.join(DATA_DIR, 'ca_consolidated.xml'),
        'error_msg': 'Network error on CA: Using cache'
    }
}

def get_un_url():
    try:
        response = requests.get(SANCTIONS_SOURCES['UN']['base_url'], timeout=10)
        response.raise_for_status()
        tree = html.fromstring(response.content)
        xml_link = tree.xpath(SANCTIONS_SOURCES['UN']['xml_path'])
        if xml_link:
            base = 'https://scsanctions.un.org'
            return base + xml_link[0] if xml_link[0].startswith('/') else xml_link[0]
        raise ValueError('No XML link found')
    except Exception as e:
        raise RuntimeError(f'Failed to get UN URL: {str(e)}')

def fetch_sanctions_list(source):
    if source == 'UN':
        try:
            url = get_un_url()
        except:
            url = None  # Fallback to cache
    else:
        url = SANCTIONS_SOURCES[source].get('url')
    
    file_path = SANCTIONS_SOURCES[source]['file']
    error_msg = SANCTIONS_SOURCES[source]['error_msg']
    
    if not url:
        if os.path.exists(file_path):
            return error_msg
        raise ValueError(f'No URL or cache for {source}')
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return f'{source} list updated.'
    except Exception:
        if os.path.exists(file_path):
            return error_msg
        raise ValueError(f'Download failed for {source}, no cache.')

def parse_xml(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'XML file missing: {file_path}')
    tree = html.parse(file_path)
    sanctions = []
    for entry in tree.xpath('//individual | //entity | //Designation | //sanctionEntity | //sdnEntry'):
        # Handle UN/CA: FIRST_NAME + SECOND_NAME
        first = entry.xpath('FIRST_NAME/text()') or entry.xpath('first_name/text()')
        second = entry.xpath('SECOND_NAME/text()') or entry.xpath('second_name/text()')
        name = ' '.join([first[0] if first else '', second[0] if second else '']).strip().lower()
        if name:
            sanctions.append(name)
            continue
        # Handle UK: Name/Name1 + Name2 + Name6
        name1 = entry.xpath('Names/Name/Name1/text()') or entry.xpath('name/Name1/text()')
        name2 = entry.xpath('Names/Name/Name2/text()') or entry.xpath('name/Name2/text()')
        name6 = entry.xpath('Names/Name/Name6/text()') or entry.xpath('name/Name6/text()')
        name = ' '.join([name1[0] if name1 else '', name2[0] if name2 else '', name6[0] if name6 else '']).strip().lower()
        if name:
            sanctions.append(name)
            continue
        # Handle EU/general: nameAlias/@wholeName or NAME
        whole = entry.xpath('nameAlias/@wholeName') or entry.xpath('NAME/text()') or entry.xpath('name/text()')
        name = whole[0].lower() if whole else ''
        if name:
            sanctions.append(name)
            continue
        # Handle US: firstName + lastName + akaList/aka/akaName
        us_first = entry.xpath('firstName/text()')
        us_last = entry.xpath('lastName/text()')
        name = ' '.join([us_first[0] if us_first else '', us_last[0] if us_last else '']).strip().lower()
        if name:
            sanctions.append(name)
        akas = entry.xpath('akaList/aka/akaName/text()')
        sanctions.extend(aka.lower() for aka in akas if aka)
    return [n for n in set(sanctions) if n]  # Dedup non-empty

def parse_csv(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'CSV file missing: {file_path}')
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        return [row[2].lower() for row in reader if len(row) > 2]

def parse_json(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'JSON file missing: {file_path}')
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return [entry['name'].lower() for entry in data.get('sanctions', []) if 'name' in entry]

def load_all_sanctions():
    all_sanctions = []
    for source, info in SANCTIONS_SOURCES.items():
        file_path = info['file']
        try:
            if file_path.endswith('.xml'):
                all_sanctions.extend(parse_xml(file_path))
            elif file_path.endswith('.csv'):
                all_sanctions.extend(parse_csv(file_path))
            elif file_path.endswith('.json'):
                all_sanctions.extend(parse_json(file_path))
        except Exception as e:
            app.logger.error(f'Skipping {source} due to parse error: {str(e)}')
    return list(set(all_sanctions))  # Dedup

SANCTIONS_LIST = load_all_sanctions()

def token_sort_similarity(name1, name2):
    tokens1 = sorted(name1.split())
    tokens2 = sorted(name2.split())
    return difflib.SequenceMatcher(None, ' '.join(tokens1), ' '.join(tokens2)).ratio() * 100

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_lists', methods=['POST'])
def update_lists():
    messages = []
    for source in SANCTIONS_SOURCES:
        try:
            messages.append(fetch_sanctions_list(source))
        except ValueError as e:
            messages.append(str(e))
    global SANCTIONS_LIST
    SANCTIONS_LIST = load_all_sanctions()
    return jsonify({'messages': messages})

@app.route('/check_sanctions', methods=['POST'])
def check_sanctions():
    data = request.json
    name = data.get('name', '').strip().lower()
    if not name or not isinstance(name, str):
        return jsonify({'error': 'Valid name required'}), 400
    candidates = difflib.get_close_matches(name, SANCTIONS_LIST, n=10, cutoff=0.6)
    results = [cand for cand in candidates if token_sort_similarity(name, cand) > 80]
    return jsonify({'matches': results})

@app.route('/sanctions_lists')
def sanctions_lists():
    return render_template('sanctions-lists.html')

@app.route('/import_consolidated', methods=['POST'])
def import_consolidated():
    files = request.files.getlist('files')
    if not files:
        flash('No files selected', 'error')
        return jsonify({'error': 'No files'}), 400
    imported = []
    for file in files:
        if not file.filename or not file.filename.lower().endswith(
                ('.xml', '.csv', '.ods', '.xlsx')):
            flash(f'Invalid file: {file.filename}', 'error')
            continue
        try:
            if file.filename.endswith('.xml'):
                content = file.read().decode('utf-8')
                tree = html.fromstring(content)
                names = parse_xml(tree)  # Reuse parse_xml logic
            elif file.filename.endswith('.csv'):
                content = file.read().decode('utf-8')
                reader = csv.reader(content.splitlines())
                names = [row[2].lower() for row in reader if len(row) > 2]
            else:  # ODS/XLSX
                df = pd.read_excel(file, engine='openpyxl' if file.filename.endswith('.xlsx') else 'odf')
                col = 'name' if 'name' in df.columns else df.columns[0]
                names = df[col].dropna().str.lower().tolist()
            global SANCTIONS_LIST
            SANCTIONS_LIST.extend(names)
            SANCTIONS_LIST = list(set(SANCTIONS_LIST))  # Dedup
            imported.append(file.filename)
            app.logger.info(f'Uploaded {file.filename} with {len(names)} names')
        except Exception as e:
            flash(f'Error importing {file.filename}: {str(e)}', 'error')
    if imported:
        flash(f'Imported: {", ".join(imported)}', 'success')
    return redirect(url_for('sanctions_lists'))

@app.route('/export_sanctions')
def export_sanctions():
    fmt = request.args.get('format', 'csv').strip().lower()
    if fmt not in ('csv', 'json', 'xml'):
        return jsonify({'error': 'Invalid format (csv/json/xml)'}), 400
    if not SANCTIONS_LIST:
        return jsonify({'error': 'No sanctions to export'}), 400
    try:
        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['name'])
            writer.writerows([[name] for name in SANCTIONS_LIST])
            resp = make_response(output.getvalue())
            resp.headers['Content-Type'] = 'text/csv'
            resp.headers['Content-Disposition'] = 'attachment; filename=sanctions.csv'
        elif fmt == 'json':
            resp = make_response(json.dumps({'sanctions': SANCTIONS_LIST}))
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Content-Disposition'] = 'attachment; filename=sanctions.json'
        else:  # xml
            xml_content = '<sanctions>' + ''.join(f'<name>{name}</name>' for name in SANCTIONS_LIST) + '</sanctions>'
            resp = make_response(xml_content)
            resp.headers['Content-Type'] = 'application/xml'
            resp.headers['Content-Disposition'] = 'attachment; filename=sanctions.xml'
        return resp
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

# For future auth: Use JWT or session-based; no logic yet.

class TestSanctionsFunctions(unittest.TestCase):
    def test_get_un_success(self):
        class MockResponse:
            status_code = 200
            content = b'<html><a href="/resources/xml/en/consolidated.xml?token=abc123">XML</a></html>'
        original_get = requests.get
        requests.get = lambda url, **kw: MockResponse()
        url = get_un_url()
        self.assertIn('?token=abc123', url)
        requests.get = original_get

    def test_get_un_failure(self):
        class MockResponse:
            status_code = 200
            content = b'<html></html>'
        original_get = requests.get
        requests.get = lambda url, **kw: MockResponse()
        with self.assertRaises(ValueError):
            get_un_url()
        requests.get = original_get

    def test_fetch_list_success(self):
        class MockResponse:
            status_code = 200
            content = b'<xml></xml>'
        original_get = requests.get
        requests.get = lambda url, **kw: MockResponse()
        result = fetch_sanctions_list('CA')
        self.assertEqual(result, 'CA list updated.')
        requests.get = original_get
        os.remove(SANCTIONS_SOURCES['CA']['file'])

    def test_fetch_list_failure_cache(self):
        file_path = SANCTIONS_SOURCES['CA']['file']
        with open(file_path, 'w') as f:
            f.write('<xml></xml>')
        class MockResponse:
            status_code = 500
        original_get = requests.get
        requests.get = lambda url, **kw: MockResponse()
        result = fetch_sanctions_list('CA')
        self.assertEqual(result, 'Network error on CA: Using cache')
        requests.get = original_get
        os.remove(file_path)

    def test_parse_xml_un(self):
        content = '<root><individual><FIRST_NAME>Eric</FIRST_NAME><SECOND_NAME>Badege</SECOND_NAME></individual></root>'
        file_path = 'test_un.xml'
        with open(file_path, 'w') as f:
            f.write(content)
        sanctions = parse_xml(file_path)
        self.assertIn('eric badege', sanctions)
        os.remove(file_path)

    def test_parse_xml_uk(self):
        content = '<Designations><Designation><Names><Name><Name1>Muhammad</Name1><Name2>Ali</Name2><Name6>Al-Qadari</Name6></Name></Names></Designation></Designations>'
        file_path = 'test_uk.xml'
        with open(file_path, 'w') as f:
            f.write(content)
        sanctions = parse_xml(file_path)
        self.assertIn('muhammad ali al-qadari', sanctions)
        os.remove(file_path)

    def test_parse_xml_eu(self):
        content = '<export><sanctionEntity><nameAlias wholeName="Saddam Hussein Al-Tikriti" /></sanctionEntity></export>'
        file_path = 'test_eu.xml'
        with open(file_path, 'w') as f:
            f.write(content)
        sanctions = parse_xml(file_path)
        self.assertIn('saddam hussein al-tikriti', sanctions)
        os.remove(file_path)

    def test_parse_xml_us(self):
        content = '<sdnList><sdnEntry><firstName>Abu</firstName><lastName>Abbas</lastName><akaList><aka><akaName>Abu Ali</akaName></aka></akaList></sdnEntry></sdnList>'
        file_path = 'test_us.xml'
        with open(file_path, 'w') as f:
            f.write(content)
        sanctions = parse_xml(file_path)
        self.assertIn('abu abbas', sanctions)
        self.assertIn('abu ali', sanctions)
        os.remove(file_path)

    def test_parse_xml_ca(self):
        content = '<CONSOLIDATED_LIST><INDIVIDUALS><INDIVIDUAL><FIRST_NAME>Irina</FIRST_NAME><SECOND_NAME>Anatolievna</SECOND_NAME><THIRD_NAME>Kostenko</THIRD_NAME></INDIVIDUAL></INDIVIDUALS></CONSOLIDATED_LIST>'
        file_path = 'test_ca.xml'
        with open(file_path, 'w') as f:
            f.write(content)
        sanctions = parse_xml(file_path)
        self.assertIn('irina anatolievna', sanctions)  # Adjust if THIRD_NAME needed
        os.remove(file_path)

    def test_parse_xml_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            parse_xml('nonexistent.xml')

    def test_parse_xml_empty_names(self):
        content = '<root><individual></individual></root>'
        file_path = 'test_empty.xml'
        with open(file_path, 'w') as f:
            f.write(content)
        sanctions = parse_xml(file_path)
        self.assertEqual(sanctions, [])
        os.remove(file_path)

    def test_token_sort_exact(self):
        score = token_sort_similarity('eric badege', 'Eric Badege')
        self.assertGreater(score, 80)

    def test_token_sort_partial(self):
        score = token_sort_similarity('frank bwambale', 'frank kakolele bwambale')
        self.assertGreater(score, 80)

    def test_check_sanctions_partial(self):
        global SANCTIONS_LIST
        SANCTIONS_LIST = ['eric badege', 'frank kakolele bwambale']
        response = app.test_client().post('/check_sanctions', json={'name': 'Eric Badege'})
        data = json.loads(response.data)
        self.assertIn('eric badege', data['matches'])

    def test_check_sanctions_no_name(self):
        response = app.test_client().post('/check_sanctions', json={})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Valid name required', data['error'])

    def test_check_sanctions_invalid_type(self):
        response = app.test_client().post('/check_sanctions', json={'name': 123})
        self.assertEqual(response.status_code, 400)

    def test_import_xml_valid(self):
        global SANCTIONS_LIST
        original_list = SANCTIONS_LIST.copy()
        bio = io.BytesIO(b'<root><individual><FIRST_NAME>Test</FIRST_NAME></individual></root>')
        response = app.test_client().post('/import_consolidated', data={'files': (bio, 'test.xml')})
        self.assertEqual(response.status_code, 302)
        self.assertIn('test', SANCTIONS_LIST)
        SANCTIONS_LIST = original_list

    def test_import_csv_valid(self):
        global SANCTIONS_LIST
        original_list = SANCTIONS_LIST.copy()
        csv_content = b'id,schema,name\n1,Person,test name'
        bio = io.BytesIO(csv_content)
        response = app.test_client().post('/import_consolidated', data={'files': (bio, 'test.csv')})
        self.assertEqual(response.status_code, 302)
        self.assertIn('test name', SANCTIONS_LIST)
        SANCTIONS_LIST = original_list

    def test_import_xlsx_valid(self):
        global SANCTIONS_LIST
        original_list = SANCTIONS_LIST.copy()
        df = pd.DataFrame({'name': ['test xlsx']})
        bio = io.BytesIO()
        df.to_excel(bio, index=False)
        bio.seek(0)
        response = app.test_client().post('/import_consolidated', data={'files': (bio, 'test.xlsx')})
        self.assertEqual(response.status_code, 302)
        self.assertIn('test xlsx', SANCTIONS_LIST)
        SANCTIONS_LIST = original_list

    def test_import_invalid_ext(self):
        bio = io.BytesIO(b'test')
        response = app.test_client().post('/import_consolidated', data={'files': (bio, 'invalid.txt')})
        self.assertEqual(response.status_code, 302)

    def test_import_empty_file(self):
        bio = io.BytesIO(b'')
        response = app.test_client().post('/import_consolidated', data={'files': (bio, 'empty.xml')})
        self.assertEqual(response.status_code, 302)

    def test_import_no_files(self):
        response = app.test_client().post('/import_consolidated')
        self.assertEqual(response.status_code, 400)

    def test_export_csv_success(self):
        global SANCTIONS_LIST
        SANCTIONS_LIST = ['test']
        response = app.test_client().get('/export_sanctions?format=csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name\ntest\n', response.data)

    def test_export_json_success(self):
        global SANCTIONS_LIST
        SANCTIONS_LIST = ['test']
        response = app.test_client().get('/export_sanctions?format=json')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'{"sanctions": ["test"]}', response.data)

    def test_export_xml_success(self):
        global SANCTIONS_LIST
        SANCTIONS_LIST = ['test']
        response = app.test_client().get('/export_sanctions?format=xml')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<sanctions><name>test</name></sanctions>', response.data)

    def test_export_invalid_format(self):
        response = app.test_client().get('/export_sanctions?format=invalid')
        self.assertEqual(response.status_code, 400)

    def test_export_empty_list(self):
        global SANCTIONS_LIST
        SANCTIONS_LIST = []
        response = app.test_client().get('/export_sanctions')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
