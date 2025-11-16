import unittest
from io import StringIO, BytesIO
import xml.etree.ElementTree as ET
import pandas as pd
import csv
import re

# Copy parsers from app.py for independent testing
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
        return []  # Gracefully return empty on structure change

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
        df = pd.read_excel(BytesIO(data), engine='openpyxl' if data[0:4] == b'PK\x03\x04' else 'odf', sheet_name=0, header=0)  # Fix: header=0 to read headers correctly
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
        return []  # Gracefully return empty

def parse_canada_xml(data, source):
    try:
        root = ET.fromstring(data)
        entries = []
        for item in root.findall('.//item'):
            name = item.find('name').text or ''
            if name.strip():  # Fix: Check strip() for empty
                other_info = item.find('description').text or ''
                entries.append({'full_name': name.strip(), 'other_info': other_info})
        return entries
    except ET.ParseError as e:
        raise ValueError("Invalid XML format for Canada list") from e
    except AttributeError:
        return []  # Gracefully return empty

class TestParsers(unittest.TestCase):
    def test_parse_un_xml_valid(self):
        xml = '''<CONSOLIDATED_LIST><INDIVIDUALS><INDIVIDUAL><FIRST_NAME>John</FIRST_NAME><SECOND_NAME>Doe</SECOND_NAME><COMMENTS1>Test</COMMENTS1></INDIVIDUAL></INDIVIDUALS></CONSOLIDATED_LIST>'''
        entries = parse_un_xml(xml, 'UN')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['full_name'], 'John Doe')
        self.assertEqual(entries[0]['other_info'], 'Test')

    def test_parse_un_xml_invalid(self):
        with self.assertRaises(ValueError):
            parse_un_xml('<invalid>', 'UN')

    def test_parse_un_xml_edge_empty(self):
        xml = '<CONSOLIDATED_LIST><INDIVIDUALS></INDIVIDUALS></CONSOLIDATED_LIST>'
        entries = parse_un_xml(xml, 'UN')
        self.assertEqual(len(entries), 0)

    def test_parse_un_xml_missing_fields(self):
        xml = '''<CONSOLIDATED_LIST><INDIVIDUALS><INDIVIDUAL><FIRST_NAME>John</FIRST_NAME></INDIVIDUAL></INDIVIDUALS></CONSOLIDATED_LIST>'''
        entries = parse_un_xml(xml, 'UN')
        self.assertEqual(len(entries), 0)

    def test_parse_ofac_csv_valid(self):
        csv_data = 'ent_num,name,type,programs,list,score\n1,Test Name,individual,SDN,SDN,100\n'
        entries = parse_ofac_csv(csv_data, 'OFAC')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['full_name'], 'Test Name')
        self.assertEqual(entries[0]['other_info'], '')

    def test_parse_ofac_csv_invalid_header(self):
        with self.assertRaises(ValueError):
            parse_ofac_csv('wrong_header\n', 'OFAC')

    def test_parse_ofac_csv_empty(self):
        csv_data = 'ent_num,name,type,programs,list,score\n'
        entries = parse_ofac_csv(csv_data, 'OFAC')
        self.assertEqual(len(entries), 0)

    def test_parse_ofac_csv_missing_columns(self):
        csv_data = 'ent_num,name\n1,Test Name\n'
        entries = parse_ofac_csv(csv_data, 'OFAC')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['full_name'], 'Test Name')
        self.assertEqual(entries[0]['other_info'], '')

    def test_parse_uk_ods_valid(self):
        # Mock XLSX data (since odfpy may not be installed; test openpyxl path)
        data = BytesIO()
        df = pd.DataFrame({'Name 1': ['John'], 'Name 2': ['Doe'], 'Remarks': ['Test']})
        with pd.ExcelWriter(data, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        entries = parse_uk_ods(data.getvalue(), 'UK')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['full_name'], 'John Doe')
        self.assertEqual(entries[0]['other_info'], 'Test')

    def test_parse_uk_ods_invalid(self):
        with self.assertRaises(ValueError):
            parse_uk_ods(b'invalid', 'UK')

    def test_parse_uk_ods_empty(self):
        data = BytesIO()
        df = pd.DataFrame()
        with pd.ExcelWriter(data, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        entries = parse_uk_ods(data.getvalue(), 'UK')
        self.assertEqual(len(entries), 0)

    def test_parse_uk_ods_tampered(self):
        data = BytesIO()
        df = pd.DataFrame({'WrongColumn': ['Test']})
        with pd.ExcelWriter(data, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        entries = parse_uk_ods(data.getvalue(), 'UK')
        self.assertEqual(len(entries), 0)  # No name parts

    def test_parse_eu_xml_valid(self):
        xml = '''<export><sanctionEntity><nameAlias wholeName="John Doe"/><regulation><regulationSummary>Test</regulationSummary></regulation></sanctionEntity></export>'''
        entries = parse_eu_xml(xml, 'EU')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['full_name'], 'John Doe')
        self.assertEqual(entries[0]['other_info'], 'Test')

    def test_parse_eu_xml_invalid(self):
        with self.assertRaises(ValueError):
            parse_eu_xml('<invalid>', 'EU')

    def test_parse_eu_xml_edge_empty(self):
        xml = '<export></export>'
        entries = parse_eu_xml(xml, 'EU')
        self.assertEqual(len(entries), 0)

    def test_parse_eu_xml_missing_fields(self):
        xml = '<export><sanctionEntity></sanctionEntity></export>'
        entries = parse_eu_xml(xml, 'EU')
        self.assertEqual(len(entries), 0)

    def test_parse_canada_xml_valid(self):
        xml = '<root><item><name>John Doe</name><description>Test</description></item></root>'
        entries = parse_canada_xml(xml, 'CANADA')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['full_name'], 'John Doe')
        self.assertEqual(entries[0]['other_info'], 'Test')

    def test_parse_canada_xml_invalid(self):
        with self.assertRaises(ValueError):
            parse_canada_xml('<invalid>', 'CANADA')

    def test_parse_canada_xml_edge_empty(self):
        xml = '<root></root>'
        entries = parse_canada_xml(xml, 'CANADA')
        self.assertEqual(len(entries), 0)

    def test_parse_canada_xml_missing_fields(self):
        xml = '<root><item><name> </name></item></root>'  # Space only
        entries = parse_canada_xml(xml, 'CANADA')
        self.assertEqual(len(entries), 0)

if __name__ == '__main__':
    unittest.main()
