# test_app.py - Concise fixes: Imports, context, mock downloads, validation raises.
import unittest
from unittest.mock import patch  # For mocking downloads (performance/no network)
from app import app, db
from models import User, Individual, Alias  # Added imports
from forms import LoginForm
from utils import update_sanctions_lists, incorporate_to_db

def mock_download(*args, **kwargs):  # Mock for tests (avoids 404)
    return 'data/mock.xml'  # Or return bytes for parse

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

    # Existing tests unchanged (login success/invalid, update_lists, invalid_username)

class TestDBIncorporation(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.drop_all()

    @patch('utils.download_file', side_effect=mock_download)  # Mock to avoid network/404
    def test_insert_individual(self, mock_download):  # Valid insert: In DB
        data = {'un_consolidated.xml': [{'ref': 'TEST001', 'name': 'Test Name', 'aliases': ['Alias1']}]}
        with app.app_context():
            incorporate_to_db(data)
            ind = Individual.query.filter_by(reference_number='TEST001').first()
            self.assertIsNotNone(ind, "Individual not inserted")
            alias = Alias.query.filter_by(alias_name='Alias1').first()
            self.assertIsNotNone(alias, "Alias not inserted")

    @patch('utils.download_file', side_effect=mock_download)
    def test_duplicate_ref_error(self, mock_download):  # Edge: Duplicate raises ValueError
        data = {'un_consolidated.xml': [{'ref': 'DUP001', 'name': 'Dup'}]}
        with app.app_context():
            incorporate_to_db(data)
            with self.assertRaises(ValueError, msg="Duplicate ref not raised"):
                incorporate_to_db(data)

    @patch('utils.download_file', side_effect=mock_download)
    def test_invalid_data_rollback(self, mock_download):  # Error: Bad type; rollback/no insert
        data = {'un_consolidated.xml': [{'ref': 'INV001', 'name': 123}]}  # Invalid
        with app.app_context():
            with self.assertRaises(ValueError, msg="Invalid data not raised"):
                incorporate_to_db(data)
            ind = Individual.query.filter_by(reference_number='INV001').first()
            self.assertIsNone(ind, "Rollback failed—invalid data inserted")

if __name__ == '__main__':
    unittest.main()
