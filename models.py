# models.py - DB models with validation/sanitization (security). Single responsibility: Define schema.
from werkzeug.security import generate_password_hash, check_password_hash
import re  # For sanitization

from extensions import db  # Import from extensions (avoids cycle)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __init__(self, username, password):
        self.username = self.sanitize_username(username)
        self.set_password(password)

    @staticmethod
    def sanitize_username(username):
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValueError("Invalid username format.")
        return username.lower()  # Normalize (security: Prevent dupes)

    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("Password too short.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    org_company = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    tax_reg = db.Column(db.String(50), nullable=False)

    def __init__(self, user_id, org_company, address, phone, tax_reg):
        self.user_id = user_id
        self.org_company = org_company.strip()
        self.address = address.strip()
        self.phone = self.sanitize_phone(phone)
        self.tax_reg = self.sanitize_tax(tax_reg)

    @staticmethod
    def sanitize_phone(phone):
        if not re.match(r'^\+?[\d\s-]{7,20}$', phone):
            raise ValueError("Invalid phone format.")
        return phone

    @staticmethod
    def sanitize_tax(tax_reg):
        if not re.match(r'^[\w-]{5,20}$', tax_reg):
            raise ValueError("Invalid tax/reg format.")
        return tax_reg

# Sanctions Schema: Normalized tables
class Individual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(50), unique=True, nullable=False)  # e.g., UN QDi.001
    name = db.Column(db.String(255), index=True)  # Main name; indexed for search
    dob = db.Column(db.Date)  # Date of birth
    nationality = db.Column(db.String(100))
    listed_on = db.Column(db.Date)  # When added to list
    source = db.Column(db.String(50))  # e.g., 'UN', 'OFAC'

class Entity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), index=True)
    type = db.Column(db.String(50))  # e.g., 'Company', 'Group'
    listed_on = db.Column(db.Date)
    source = db.Column(db.String(50))

class Alias(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    individual_id = db.Column(db.Integer, db.ForeignKey('individual.id'))
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'))
    alias_name = db.Column(db.String(255), index=True)  # Indexed for search

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    individual_id = db.Column(db.Integer, db.ForeignKey('individual.id'))
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'))
    address = db.Column(db.String(255))
    country = db.Column(db.String(100))

class Sanction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    individual_id = db.Column(db.Integer, db.ForeignKey('individual.id'))
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'))
    program = db.Column(db.String(100))  # e.g., 'UN Al-Qaida', 'OFAC SDN'
    description = db.Column(db.Text)  # Details/reasons
