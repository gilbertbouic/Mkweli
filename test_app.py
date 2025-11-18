# test_app.py - Tests: Run python -m unittest test_app.py (feedback: "OK" or "FAIL: details").
import unittest
from app import app, db
from models import User
from forms import LoginForm

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

    def test_login_success(self):  # What: Valid flow; expect redirect/feedback
        response = self.client.post('/login', data={'username': 'test@example.com', 'password': 'testpass123'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('dashboard', response.location)  # Flow check

    def test_login_invalid(self):  # Edge: Wrong creds; expect feedback
        response = self.client.post('/login', data={'username': 'test@example.com', 'password': 'wrong'})
        self.assertIn(b'Invalid credentials', response.data)

    def test_update_lists(self):  # What: Sanctions update; edge: Handles errors
        self.client.post('/login', data={'username': 'test@example.com', 'password': 'testpass123'})  # Login first
        response = self.client.post('/update_lists')
        self.assertEqual(response.status_code, 302)  # Redirect on success/error

    def test_invalid_username(self):  # Edge: Model validation error
        with self.assertRaises(ValueError):
            User(username='invalid<script>', password='pass12345')

if __name__ == '__main__':
    unittest.main()
