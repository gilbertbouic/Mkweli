# test_app.py - Tests app features. Run: python -m unittest test_app.py (Ubuntu/Win/Mac).
# Feedback: "OK" = success; "FAIL: test_name (AssertionError: details)" = describes issue.

import unittest
import os
from unittest.mock import patch, MagicMock
from app import app
from extensions import db
from models import User, Individual, Alias  # Added
from forms import LoginForm
from utils import update_sanctions_lists, incorporate_to_db
import pandas as pd  # Added for client test
from io import BytesIO  # Added for PDF buffer

def mock_download(*args, **kwargs):  # Mock: Avoid real downloads
    return 'data/mock.xml'  # Fake path

class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():  # Push context to register app with db (fixes RuntimeError)
            db.create_all()
            user = User(username='test@example.com', password='testpass123')
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.drop_all()
        # Cleanup test.csv if exists (best option: simple check + remove; safe, cross-platform, no try/except needed for low-tech)
        if os.path.exists('test.csv'):
            os.remove('test.csv')

    def test_login_success(self):  # Valid: Redirect/feedback
        response = self.client.post('/login', data={'username': 'test@example.com', 'password': 'testpass123'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('dashboard', response.location)

    def test_login_invalid(self):  # Edge: Wrong pw; error feedback
        response = self.client.post('/login', data={'username': 'test@example.com', 'password': 'wrong'})
        self.assertIn(b'Invalid credentials', response.data)

    def test_update_lists(self):  # Update: Redirect; edge error handle
        self.client.post('/login', data={'username': 'test@example.com', 'password': 'testpass123'})
        response = self.client.post('/update_lists')
        self.assertEqual(response.status_code, 302)

    def test_invalid_username(self):  # Edge: Validation raise
        with self.assertRaises(ValueError):
            User(username='invalid<script>', password='pass12345')

    def test_debugger_disabled(self):  # Security: No debug in prod config
        self.assertFalse(app.config['DEBUG'], "Debug should be False in prod")

    def test_form_resource_limit(self):  # Performance/Security: Large input handled
        with patch.dict(app.config, {'MAX_CONTENT_LENGTH': 1}):
            response = self.client.post('/login', data={'username': 'a' * 10})
            self.assertEqual(response.status_code, 413)  # Request Entity Too Large

    def test_safe_path_windows(self):  # Security: No traversal on Windows
        import sys
        original_platform = sys.platform
        sys.platform = 'win32'
        try:
            from utils import download_file
            with self.assertRaises(ValueError):
                download_file('https://evil/../url', '../../badfile')
        finally:
            sys.platform = original_platform

    def test_jinja_injection(self):  # Security: No attr injection
        from flask import render_template_string
        template = "{{ {'onload': '<script>alert(1)</script>'} | xmlattr }}"  # Sim user input dict
        with app.app_context():
            result = render_template_string(template)
            self.assertNotIn('<script>', result)  # Escaped

    def test_requests_verify(self):  # Security: Verify enabled
        from utils import download_file
        with patch('requests.get') as mock_get:
            try:
                download_file('https://example.com', 'test.xml')
            except:
                pass
            mock_get.assert_called_with('https://example.com', timeout=10, verify=True)

    @patch('pandas.read_csv', return_value=pd.DataFrame([{'name': 'Test Name', 'dob': '2000-01-01', 'nationality': 'Test'}]))
    @patch('utils.perform_screening', return_value=[{'client_name': 'Test', 'match_name': 'Match', 'score': 85, 'dob_match': True, 'nationality_match': True, 'aliases': [], 'source': 'UN'}])
    @patch('utils.generate_pdf_report', return_value=BytesIO(b'test pdf'))
    def test_clients_screening(self, mock_report, mock_screening, mock_read):
        self.client.post('/login', data={'username': 'test@example.com', 'password': 'testpass123'})
        with open('test.csv', 'wb') as f:
            f.write(b'test')
        with open('test.csv', 'rb') as f:
            response = self.client.post('/clients', data={'file': f})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test pdf', response.data)  # Sim PDF send

class TestDBIncorporation(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    @patch('utils.download_file', side_effect=mock_download)  # Mock: No network/404
    def test_insert_individual(self, mock_download):  # Valid insert: In DB
        data = {'un_consolidated.xml': [{'type': 'individual', 'ref': 'TEST001', 'name': 'Test Name', 'aliases': ['Alias1']}]}
        with app.app_context():
            incorporate_to_db(data)
            ind = Individual.query.filter_by(reference_number='TEST001').first()
            self.assertIsNotNone(ind)
            alias = Alias.query.filter_by(alias_name='Alias1').first()
            self.assertIsNotNone(alias)

    @patch('utils.download_file', side_effect=mock_download)
    def test_duplicate_ref_error(self, mock_download):  # Edge: Duplicate raise
        data = {'un_consolidated.xml': [{'type': 'individual', 'ref': 'DUP001', 'name': 'Dup'}]}
        with app.app_context():
            incorporate_to_db(data)
            with self.assertRaises(ValueError):
                incorporate_to_db(data)

    @patch('utils.download_file', side_effect=mock_download)
    def test_invalid_data_rollback(self, mock_download):  # Error: Bad input; no insert
        data = {'un_consolidated.xml': [{'type': 'individual', 'ref': 'INV001', 'name': 123}]}
        with app.app_context():
            with self.assertRaises(ValueError):
                incorporate_to_db(data)
            ind = Individual.query.filter_by(reference_number='INV001').first()
            self.assertIsNone(ind)

if __name__ == '__main__':
    unittest.main()
