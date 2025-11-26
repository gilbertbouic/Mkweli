# models.py - DB models with validation/sanitization (security). Single responsibility: Define schema.
from werkzeug.security import generate_password_hash, check_password_hash
import re
from datetime import datetime

from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    user_details = db.relationship('UserDetails', uselist=False, backref='user', cascade='all, delete-orphan')

    def __init__(self, username, password):
        self.username = self.sanitize_username(username)
        self.set_password(password)

    @staticmethod
    def sanitize_username(username):
        username = username.strip()
        if len(username) < 3 or len(username) > 150 or not re.match(r'^[\w.@+-]+$', username):
            raise ValueError("Invalid username: 3-150 chars, alphanumeric with @.+-.")
        return username.lower()

    def set_password(self, password):
        password = password.strip()
        if len(password) < 12 or not re.search(r'[A-Z]', password) or not re.search(r'[0-9]', password) or not re.search(r'[!@#$%^&*]', password):
            raise ValueError("Password must be 12+ chars with uppercase, digit, and special char.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    org_company = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    tax_reg = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, user_id, org_company=None, address=None, phone=None, tax_reg=None):
        self.user_id = user_id
        self.org_company = org_company.strip() if org_company else None
        self.address = address.strip() if address else None
        self.phone = self._validate_phone(phone) if phone else None
        self.tax_reg = self._validate_tax_reg(tax_reg) if tax_reg else None

    @staticmethod
    def _validate_phone(phone):
        if phone:
            phone_clean = phone.strip()
            if not re.match(r'^\+?[\d\s-]{7,20}$', phone_clean):
                raise ValueError("Invalid phone format. Use: +1-234-567-8900 or similar.")
            return phone_clean
        return None

    @staticmethod
    def _validate_tax_reg(tax_reg):
        if tax_reg:
            tax_clean = tax_reg.strip()
            if not re.match(r'^[\w-]{5,20}$', tax_clean):
                raise ValueError("Invalid tax/registration format. Use 5-20 alphanumeric or hyphens.")
            return tax_clean
        return None

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip = db.Column(db.String(64))
    report_hash = db.Column(db.String(64))

    def __init__(self, user_id, action, ip=None, report_hash=None, timestamp=None):
        if not action.strip():
            raise ValueError("Action required for log.")
        self.user_id = user_id
        self.action = action.strip()[:255]
        self.ip = ip[:64] if ip else None
        self.report_hash = report_hash[:64] if report_hash else None
        self.timestamp = timestamp or datetime.utcnow()

class Individual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), index=True)
    dob = db.Column(db.Date)
    nationality = db.Column(db.String(100))
    listed_on = db.Column(db.Date)
    source = db.Column(db.String(50))

class Entity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), index=True)
    type = db.Column(db.String(50))
    listed_on = db.Column(db.Date)
    source = db.Column(db.String(50))

class Alias(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    individual_id = db.Column(db.Integer, db.ForeignKey('individual.id'))
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'))
    alias_name = db.Column(db.String(255), index=True)

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
    program = db.Column(db.String(100))
    description = db.Column(db.Text)


class ScreeningReport(db.Model):
    """Track individual client screenings with details"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_name = db.Column(db.String(255), nullable=False)
    client_type = db.Column(db.String(50))  # individual or company
    matches_found = db.Column(db.Integer, default=0)
    match_details = db.Column(db.Text)  # JSON string of match results
    screening_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    report_hash = db.Column(db.String(64))  # SHA256 hash for verification
    ip_address = db.Column(db.String(64))

    def to_dict(self):
        return {
            'id': self.id,
            'client_name': self.client_name,
            'client_type': self.client_type,
            'matches_found': self.matches_found,
            'screening_time': self.screening_time.isoformat() if self.screening_time else None,
            'report_hash': self.report_hash
        }


class ReportLog(db.Model):
    """Track daily/monthly report generation activities"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # daily or monthly
    report_date = db.Column(db.Date, nullable=False)
    total_screenings = db.Column(db.Integer, default=0)
    total_matches = db.Column(db.Integer, default=0)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'report_type': self.report_type,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'total_screenings': self.total_screenings,
            'total_matches': self.total_matches,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }
