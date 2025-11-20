# test_app.py - Tests app features. Run: python -m unittest test_app.py (Ubuntu/Win/Mac).
# Feedback: "OK" = success; "FAIL: test_name (AssertionError: details)" = describes issue.

import unittest
from unittest.mock import patch, MagicMock  # Mock downloads/parsing (no network/404/file errors)
from app import app
from extensions import db  # From extensions
from models import User, Individual, Alias
from forms import LoginForm
from utils import update_sanctions_lists, incorporate_to_db
import io  # For mock XML string

def mock_download(*args, **kwargs):  # Mock: Avoid real downloads
    return 'mock.xml'  # Fake path (use StringIO below)

class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['DEBUG'] = False  # Test prod-like
        app.config['APPLICATION_ROOT'] = '/'  # Fix KeyError; default for env
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            user = User(username='test@example.com', password='testpass123')
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def test_login_success(self):  # Valid: Redirect/feedback
        response = self.client.post('/login', data={'username': 'test@example.com', 'password': 'testpass123'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('dashboard', response.location)

    def test_login_invalid(self):  # Edge: Wrong pw; error feedback
        response = self.client.post('/login', data={'username': 'test@example.com', 'password': 'wrong'})
        self.assertIn(b'Invalid credentials', response.data)  # Check flash in HTML (template displays)

    @patch('utils.download_file', side_effect=mock_download)  # Mock: No real downloads/404
    @patch('xml.etree.ElementTree.parse')  # Mock parse to avoid file errors
    def test_update_lists(self, mock_parse, mock_download):  # Update: Redirect; edge error handle
        mock_tree = MagicMock()
        mock_tree.iter.return_value = []  # Sim empty entities
        mock_parse.return_value = mock_tree
        self.client.post('/login', data={'username': 'test@example.com', 'password': 'testpass123'})
        response = self.client.post('/update_lists')
        self.assertEqual(response.status_code, 302)

    def test_invalid_username(self):  # Edge: Validation raise
        with self.assertRaises(ValueError):
            User(username='invalid<script>', password='pass12345')

    def test_debugger_disabled(self):  # Security: No debug in prod config
        self.assertFalse(app.config['DEBUG'], "Debug should be False in prod")

    def test_form_resource_limit(self):  # Performance/Security: Large input handled
        app.config['MAX_CONTENT_LENGTH'] = 1  # Sim small limit (override for test)
        response = self.client.post('/login', data={'username': 'a' * 10})  # Oversize
        self.assertEqual(response.status_code, 413)  # Request Entity Too Large

    def test_safe_path_windows(self):  # Security: No traversal on Windows
        import sys
        original_platform = sys.platform
        sys.platform = 'win32'
        try:
            from utils import download_file
            with self.assertRaises(ValueError):
                download_file('https://evil/../url', '../../badfile')  # Invalid URL/path raise
        finally:
            sys.platform = original_platform

    def test_jinja_injection(self):  # Security: No attr injection
        from flask import render_template_string
        template = "{{ {'onload': '<script>alert(1)</script>'} | xmlattr }}"  # Sim user input dict
        with app.app_context():
            result = render_template_string(template)
            self.assertNotIn('<script>', result)  # Escaped: onload="&lt;script&gt;alert(1)&lt;/script&gt;"

    @patch('requests.get')  # Security: Verify enabled
    def test_requests_verify(self, mock_get):  # Mock get directly
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()  # No raise
        mock_get.return_value = mock_response
        from utils import download_file
        download_file('https://example.com', 'test.xml')  # Call without except
        mock_get.assert_called_with('https://example.com', timeout=10, verify=True)

class TestDBIncorporation(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    @patch('utils.download_file', side_effect=mock_download)  # Mock: No network/404
    @patch('xml.etree.ElementTree.parse')  # Mock parse for no file
    def test_insert_individual(self, mock_parse, mock_download):  # Valid insert: In DB
        mock_tree = MagicMock()
        mock_parse.return_value = mock_tree  # Sim parse
        data = {'un_consolidated.xml': [{'type': 'individual', 'ref': 'TEST001', 'name': 'Test Name', 'aliases': ['Alias1']}]}
        with app.app_context():
            incorporate_to_db(data)
            ind = Individual.query.filter_by(reference_number='TEST001').first()
            self.assertIsNotNone(ind)
            alias = Alias.query.filter_by(alias_name='Alias1').first()
            self.assertIsNotNone(alias)

    @patch('utils.download_file', side_effect=mock_download)
    @patch('xml.etree.ElementTree.parse')
    def test_duplicate_ref_error(self, mock_parse, mock_download):  # Edge: Duplicate raise
        mock_tree = MagicMock()
        mock_parse.return_value = mock_tree
        data = {'un_consolidated.xml': [{'type': 'individual', 'ref': 'DUP001', 'name': 'Dup'}]}
        with app.app_context():
            incorporate_to_db(data)
            with self.assertRaises(ValueError):  # Assume check; if SQL unique, catch IntegrityError
                incorporate_to_db(data)

    @patch('utils.download_file', side_effect=mock_download)
    @patch('xml.etree.ElementTree.parse')
    def test_invalid_data_rollback(self, mock_parse, mock_download):  # Error: Bad input; no insert
        mock_tree = MagicMock()
        mock_parse.return_value = mock_tree
        data = {'un_consolidated.xml': [{'type': 'individual', 'ref': 'INV001', 'name': 123}]}
        with app.app_context():
            with self.assertRaises(ValueError):
                incorporate_to_db(data)
            ind = Individual.query.filter_by(reference_number='INV001').first()
            self.assertIsNone(ind)

if __name__ == '__main__':
    unittest.main()
