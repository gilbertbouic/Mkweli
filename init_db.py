#!/usr/bin/env python3
"""
Initialize the database
"""
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

# Import the main app from app.py (not from app/ directory)
from app import app, db, User  # Import from app.py in the root directory

def init_database():
    """Initialize the database"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Create admin user if it doesn't exist
        from werkzeug.security import generate_password_hash
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created (password: admin123)")
        else:
            print("✅ Admin user already exists")

if __name__ == '__main__':
    init_database()
