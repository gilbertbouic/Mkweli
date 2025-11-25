#!/usr/bin/env python3
"""
Initialize database - Direct approach
"""
import os
import sys
from werkzeug.security import generate_password_hash

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import Flask and create app instance directly
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create the same app configuration as in app.py
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mkweli-secure-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mkweli.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the same models as in app.py
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))
    
def init_database():
    """Initialize the database"""
    print("🔧 Initializing Mkweli AML Database...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created")
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created (username: admin, password: admin123)")
        else:
            print("✅ Admin user already exists")
        
        print("🎉 Database initialization complete!")

if __name__ == '__main__':
    init_database()
