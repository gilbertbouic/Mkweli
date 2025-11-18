# models.py - DB models with input validation/sanitization (security).
from werkzeug.security import generate_password_hash, check_password_hash
import re  # For sanitization

from app import db  # Import db (safe: app defines it first)

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
