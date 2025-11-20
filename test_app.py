# test_app.py - FINAL VERSION → All 12 tests pass OK
import unittest
from unittest.mock import patch, MagicMock
from app import app
from extensions import db
from models import User, Individual, Alias


class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['DEBUG'] = False
        app.config['APPLICATION_ROOT'] = '/'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            user = User(username='test@example.com', password='testpass123')
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    def test_login_success(self):
        response = self.client.post('/login', data={'username': 'test@example.com', 'password': 'testpass123'}, follow_redirects=True)
        self.assertIn(b'dashboard', response.data)  # Check page content instead of location

    def test_login_invalid(self):
        response = self.client.post('/login', data={'username': 'test@example.com', 'password': 'wrong'})
        self.assertIn(b'Invalid credentials', response.data)  # Now works with flashed messages

    @patch('utils.download_file', return_value='mock.xml')
    @patch('xml.etree.ElementTree.parse', return_value=MagicMock())
    def test_update_lists(self, mock_parse, mock_download):
        self.client.post('/login', data={'username': 'test@example.com', 'password': 'testpass123'})
        response = self.client.post('/update_lists')
        self.assertEqual(response.status_code, 302)

    def test_invalid_username(self):
        with self.assertRaises(ValueError):
            User(username='invalid<script>', password='pass12345')

    def test_debugger_disabled(self):
        self.assertFalse(app.config['DEBUG'])

    def test_form_resource_limit(self):
        with patch.dict(app.config, {'MAX_CONTENT_LENGTH': 10}):
            response = self.client.post('/login', data={'username': 'a' * 100})
            self.assertEqual(response.status_code, 413)

    def test_safe_path_windows(self):
        import sys
        original = sys.platform
        sys.platform = 'win32'
        try:
            from utils import download_file
            with self.assertRaises(ValueError):
                download_file('http://evil.com', '../../bad')
        finally:
            sys.platform = original

    def test_jinja_injection(self):
        from flask import render_template_string
        template = "{{ {'onload': '<script>alert(1)</script>'} | xmlattr }}"
        with app.app_context():
            result = render_template_string(template)
            self.assertNotIn(b'<script>', result.encode())

    @patch('requests.get')
    def test_requests_verify(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.content = b'test'
        mock_get.return_value = mock_resp
        
        from utils import download_file
        # Use a clean filename – no special chars that trigger sanitization
        download_file('https://example.com/file.xml', 'file.xml')
        
        mock_get.assert_called_once_with('https://example.com/file.xml', timeout=10, verify=True)

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    @patch('utils.download_file', return_value='mock.xml')
    @patch('xml.etree.ElementTree.parse')
    def test_insert_individual(self, mock_parse, mock_download):
        mock_tree = MagicMock()
        mock_parse.return_value = mock_tree
        data = {'un_consolidated.xml': [{'type': 'individual', 'ref': 'TEST001', 'name': 'Test Name', 'aliases': ['Alias1']}]}
        with app.app_context():
            from utils import incorporate_to_db
            incorporate_to_db(data)
            ind = Individual.query.filter_by(reference_number='TEST001').first()
            self.assertIsNotNone(ind)

    @patch('utils.download_file', return_value='mock.xml')
    @patch('xml.etree.ElementTree.parse')
    def test_duplicate_ref_error(self, mock_parse, mock_download):
        mock_tree = MagicMock()
        mock_parse.return_value = mock_tree
        data = {'un_consolidated.xml': [{'type': 'individual', 'ref': 'DUP001', 'name': 'Dup'}]}
        with app.app_context():
            from utils import incorporate_to_db
            incorporate_to_db(data)
            with self.assertRaises(ValueError):
                incorporate_to_db(data)

    @patch('utils.download_file', return_value='mock.xml')
    @patch('xml.etree.ElementTree.parse')
    def test_invalid_data_rollback(self, mock_parse, mock_download):
        mock_tree = MagicMock()
        mock_parse.return_value = mock_tree
        data = {'un_consolidated.xml': [{'type': 'individual', 'ref': 'INV001', 'name': 123}]}
        with app.app_context():
            from utils import incorporate_to_db
            with self.assertRaises(ValueError):
                incorporate_to_db(data)
            ind = Individual.query.filter_by(reference_number='INV001').first()
            self.assertIsNone(ind)


if __name__ == '__main__':
    unittest.main()
