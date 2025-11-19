# test_app.py - Tests app features. Run: python -m unittest test_app.py (Ubuntu/Win/Mac).
# Feedback: "OK" = success; "FAIL: test_name (AssertionError: details)" = describes issue.

import unittest
from unittest.mock import patch  # Mock downloads (no network/404)
from app import app, db
from models import User, Individual, Alias  # Added
from forms import LoginForm
from utils import update_sanctions_lists, incorporate_to_db

def mock_download(*args, **kwargs):  # Mock: Avoid real downloads
    return 'data/mock.xml'  # Fake path

class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
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
        self.assertIn(b'Invalid credentials', response.data)

    def test_update_lists(self):  # Update: Redirect; edge error handle
        self.client.post('/login', data={'username': 'test@example.com', 'password': 'testpass123'})
        response = self.client.post('/update_lists')
        self.assertEqual(response.status_code, 302)

    def test_invalid_username(self):  # Edge: Validation raise
        with self.assertRaises(ValueError):
            User(username='invalid<script>', password='pass12345')

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
        data = {'un_consolidated.xml': [{'ref': 'TEST001', 'name': 'Test Name', 'aliases': ['Alias1']}]}
        with app.app_context():
            incorporate_to_db(data)
            ind = Individual.query.filter_by(reference_number='TEST001').first()
            self.assertIsNotNone(ind)
            alias = Alias.query.filter_by(alias_name='Alias1').first()
            self.assertIsNotNone(alias)

    @patch('utils.download_file', side_effect=mock_download)
    def test_duplicate_ref_error(self, mock_download):  # Edge: Duplicate raise
        data = {'un_consolidated.xml': [{'ref': 'DUP001', 'name': 'Dup'}]}
        with app.app_context():
            incorporate_to_db(data)
            with self.assertRaises(ValueError):
                incorporate_to_db(data)

    @patch('utils.download_file', side_effect=mock_download)
    def test_invalid_data_rollback(self, mock_download):  # Error: Bad input; no insert
        data = {'un_consolidated.xml': [{'ref': 'INV001', 'name': 123}]}
        with app.app_context():
            with self.assertRaises(ValueError):
                incorporate_to_db(data)
            ind = Individual.query.filter_by(reference_number='INV001').first()
            self.assertIsNone(ind)

if __name__ == '__main__':
    unittest.main()
