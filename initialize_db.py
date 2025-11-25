#!/usr/bin/env python3
"""
Initialize database for Mkweli AML System
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import the main app
from app import app, db, User
from werkzeug.security import generate_password_hash

def initialize_database():
    """Initialize the database with required tables and admin user"""
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
    initialize_database()
