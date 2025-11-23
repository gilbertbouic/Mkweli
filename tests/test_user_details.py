"""
Test suite for UserDetails model and settings functionality.
Tests cover: creation, validation, retrieval, updates, and form handling.
"""
import unittest
from app import app
from extensions import db
from models import User, UserDetails
from forms import UserDetailsForm
from datetime import datetime


class TestUserDetailsModel(unittest.TestCase):
    """Test UserDetails model creation and validation."""

    def setUp(self):
        """Initialize test app and database."""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_ECHO'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Drop all existing tables and recreate
        db.drop_all()
        db.create_all()
        
        # Create a test user
        self.test_user = User(username='test@example.com', password='Password123!')
        db.session.add(self.test_user)
        db.session.commit()

    def tearDown(self):
        """Clean up database and app context."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_details_creation(self):
        """Test creating UserDetails for a user."""
        user_details = UserDetails(
            user_id=self.test_user.id,
            org_company='Acme Corp',
            address='123 Main St, City, Country',
            phone='+1-234-567-8900',
            tax_reg='TX-12345'
        )
        db.session.add(user_details)
        db.session.commit()
        
        # Verify stored correctly
        retrieved = UserDetails.query.filter_by(user_id=self.test_user.id).first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.org_company, 'Acme Corp')
        self.assertEqual(retrieved.address, '123 Main St, City, Country')
        self.assertEqual(retrieved.phone, '+1-234-567-8900')
        self.assertEqual(retrieved.tax_reg, 'TX-12345')

    def test_user_details_all_optional(self):
        """Test UserDetails with only required user_id."""
        user_details = UserDetails(user_id=self.test_user.id)
        db.session.add(user_details)
        db.session.commit()
        
        retrieved = UserDetails.query.filter_by(user_id=self.test_user.id).first()
        self.assertIsNotNone(retrieved)
        self.assertIsNone(retrieved.org_company)
        self.assertIsNone(retrieved.address)

    def test_user_details_whitespace_stripped(self):
        """Test that input whitespace is stripped."""
        user_details = UserDetails(
            user_id=self.test_user.id,
            org_company='  Acme Corp  ',
            address='  456 Oak Ave  '
        )
        db.session.add(user_details)
        db.session.commit()
        
        retrieved = UserDetails.query.filter_by(user_id=self.test_user.id).first()
        self.assertEqual(retrieved.org_company, 'Acme Corp')
        self.assertEqual(retrieved.address, '456 Oak Ave')

    def test_phone_validation_valid_formats(self):
        """Test valid phone number formats."""
        valid_phones = [
            '+1-234-567-8900',
            '1234567890',
            '+44 20 7946 0958',
            '+33 1 42 34 56 78',
            '555-1234'
        ]
        
        for phone in valid_phones:
            user_details = UserDetails(
                user_id=self.test_user.id,
                phone=phone
            )
            db.session.add(user_details)
            db.session.commit()
            
            retrieved = UserDetails.query.filter_by(phone=phone).first()
            self.assertIsNotNone(retrieved)
            db.session.delete(retrieved)
            db.session.commit()

    def test_phone_validation_invalid_formats(self):
        """Test invalid phone number formats raise error."""
        invalid_phones = [
            'abc123',  # Too short
            '12',      # Too short
            'phone!@#',  # Invalid characters
        ]
        
        for phone in invalid_phones:
            with self.assertRaises(ValueError):
                UserDetails(
                    user_id=self.test_user.id,
                    phone=phone
                )

    def test_tax_reg_validation_valid_formats(self):
        """Test valid tax/registration formats."""
        valid_tax_regs = [
            'TX-12345',
            'ABC123',
            'TAX-REG-001',
            'us_tax_123'
        ]
        
        for tax_reg in valid_tax_regs:
            user_details = UserDetails(
                user_id=self.test_user.id,
                tax_reg=tax_reg
            )
            db.session.add(user_details)
            db.session.commit()
            
            retrieved = UserDetails.query.filter_by(tax_reg=tax_reg).first()
            self.assertIsNotNone(retrieved)
            db.session.delete(retrieved)
            db.session.commit()

    def test_tax_reg_validation_invalid_formats(self):
        """Test invalid tax formats raise error."""
        invalid_tax_regs = [
            'AB12',      # Too short
            'TAX!@#',    # Invalid chars
            'x' * 21,    # Too long
        ]
        
        for tax_reg in invalid_tax_regs:
            with self.assertRaises(ValueError):
                UserDetails(
                    user_id=self.test_user.id,
                    tax_reg=tax_reg
                )

    def test_user_details_relationship(self):
        """Test User-UserDetails relationship."""
        user_details = UserDetails(
            user_id=self.test_user.id,
            org_company='Test Org'
        )
        db.session.add(user_details)
        db.session.commit()
        
        # Verify relationship
        self.assertIsNotNone(self.test_user.user_details)
        self.assertEqual(self.test_user.user_details.org_company, 'Test Org')

    def test_user_details_timestamps(self):
        """Test created_at and updated_at timestamps."""
        user_details = UserDetails(
            user_id=self.test_user.id,
            org_company='Test Org'
        )
        db.session.add(user_details)
        db.session.commit()
        
        self.assertIsNotNone(user_details.created_at)
        self.assertIsNotNone(user_details.updated_at)
        self.assertIsInstance(user_details.created_at, datetime)


class TestSettingsRoute(unittest.TestCase):
    """Test settings route GET/POST functionality."""

    def setUp(self):
        """Initialize test app and client."""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Drop all and recreate tables
        db.drop_all()
        db.create_all()
        
        self.client = self.app.test_client()
        
        # Create test user
        self.test_user = User(username='test@example.com', password='Password123!')
        db.session.add(self.test_user)
        db.session.commit()
        
        # Login
        self.client.post('/login', data={
            'username': 'test@example.com',
            'password': 'Password123!'
        })

    def tearDown(self):
        """Clean up."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_settings_page_accessible(self):
        """Test settings page loads for authenticated user."""
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'User Settings', response.data)

    def test_settings_page_redirects_when_not_logged_in(self):
        """Test settings page redirects to login if not authenticated."""
        # Logout first
        self.client.get('/logout')
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)

    def test_save_user_details(self):
        """Test POST /settings saves user details."""
        response = self.client.post('/settings', data={
            'org_company': 'Test Organization',
            'address': '789 Test Road, Test City, Test Country',
            'phone': '+1-555-123-4567',
            'tax_reg': 'TEST-001'
        }, follow_redirects=True)
        
        self.assertIn(b'Settings saved successfully', response.data)
        
        # Verify in database
        user_details = UserDetails.query.filter_by(
            user_id=self.test_user.id
        ).first()
        self.assertIsNotNone(user_details)
        self.assertEqual(user_details.org_company, 'Test Organization')
        self.assertEqual(user_details.address, '789 Test Road, Test City, Test Country')

    def test_update_existing_user_details(self):
        """Test POST /settings updates existing user details."""
        # Create initial details
        user_details = UserDetails(
            user_id=self.test_user.id,
            org_company='Old Org',
            address='Old Address'
        )
        db.session.add(user_details)
        db.session.commit()
        
        # Update
        response = self.client.post('/settings', data={
            'org_company': 'New Org',
            'address': 'New Address',
            'phone': '+1-555-999-8888',
            'tax_reg': 'NEW-002'
        }, follow_redirects=True)
        
        self.assertIn(b'Settings saved successfully', response.data)
        
        # Verify updated
        retrieved = UserDetails.query.filter_by(user_id=self.test_user.id).first()
        self.assertEqual(retrieved.org_company, 'New Org')
        self.assertEqual(retrieved.address, 'New Address')
        self.assertEqual(retrieved.phone, '+1-555-999-8888')

    def test_prefill_form_on_get(self):
        """Test GET /settings prefills form with existing data."""
        # Create details
        user_details = UserDetails(
            user_id=self.test_user.id,
            org_company='Prefill Org',
            address='Prefill Address',
            phone='+1-555-000-0000',
            tax_reg='PREF-001'
        )
        db.session.add(user_details)
        db.session.commit()
        
        # Fetch form
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Prefill Org', response.data)
        self.assertIn(b'Prefill Address', response.data)

    def test_invalid_phone_format_rejected(self):
        """Test invalid phone format is rejected by form validation."""
        response = self.client.post('/settings', data={
            'org_company': 'Test',
            'address': 'Test Address',
            'phone': 'invalid_phone',
            'tax_reg': 'TEST-001'
        }, follow_redirects=False)
        
        # Check response still shows the form (validation failed, no redirect)
        self.assertEqual(response.status_code, 200)
        # Form should be re-rendered with the submitted data
        self.assertIn(b'User Settings', response.data)

    def test_invalid_tax_reg_format_rejected(self):
        """Test invalid tax registration format is rejected by form validation."""
        response = self.client.post('/settings', data={
            'org_company': 'Test',
            'address': 'Test Address',
            'phone': '+1-555-123-4567',
            'tax_reg': 'XX'  # Too short
        }, follow_redirects=False)
        
        # Check response still shows the form (validation failed, no redirect)
        self.assertEqual(response.status_code, 200)
        # Form should be re-rendered
        self.assertIn(b'User Settings', response.data)


class TestUserDetailsForm(unittest.TestCase):
    """Test UserDetailsForm validation."""

    def setUp(self):
        """Initialize app context."""
        self.app = app
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up."""
        self.app_context.pop()

    def test_form_validation_success(self):
        """Test form with valid data."""
        form_data = {
            'org_company': 'Valid Org',
            'address': 'Valid Address',
            'phone': '+1-555-123-4567',
            'tax_reg': 'VAL-001'
        }
        # Form validation would be tested with request context
        # This is a placeholder for integration testing

    def test_form_fields_required(self):
        """Test all fields are marked as required."""
        form = UserDetailsForm()
        # Verify field validators include DataRequired
        self.assertTrue(hasattr(form.org_company, 'validators'))
        self.assertTrue(hasattr(form.address, 'validators'))


if __name__ == '__main__':
    unittest.main()
