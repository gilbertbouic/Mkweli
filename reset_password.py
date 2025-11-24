#!/usr/bin/env python3
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from werkzeug.security import generate_password_hash

# Try to import User model - adjust based on your actual model location
try:
    from app.models import User
except ImportError:
    try:
        from models import User
    except ImportError:
        print("Could not import User model. Checking available models...")
        # Let's see what models are available
        with app.app_context():
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Available tables: {tables}")
            sys.exit(1)

def reset_password():
    with app.app_context():
        # Check if User table exists and has the right structure
        try:
            # Try to find any user
            user = User.query.first()
            
            if user:
                print(f"Found user: {user.username if hasattr(user, 'username') else 'N/A'}")
                # Reset password
                new_password = "admin123"  # Change this to your desired password
                if hasattr(user, 'password_hash'):
                    user.password_hash = generate_password_hash(new_password)
                elif hasattr(user, 'password'):
                    user.password = generate_password_hash(new_password)
                else:
                    print("No password field found in User model")
                    return
                
                db.session.commit()
                print(f"Password reset successfully to: {new_password}")
            else:
                # Create a new admin user
                print("No users found. Creating admin user...")
                new_password = "admin123"
                
                # Create user based on available attributes
                user_attrs = {}
                if hasattr(User, 'username'):
                    user_attrs['username'] = 'admin'
                if hasattr(User, 'email'):
                    user_attrs['email'] = 'admin@example.com'
                
                user = User(**user_attrs)
                
                if hasattr(user, 'password_hash'):
                    user.password_hash = generate_password_hash(new_password)
                elif hasattr(user, 'password'):
                    user.password = generate_password_hash(new_password)
                
                db.session.add(user)
                db.session.commit()
                print(f"Admin user created with password: {new_password}")
                
        except Exception as e:
            print(f"Error: {e}")
            print("Let's check the database structure...")
            
            # Inspect the database
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {tables}")
            
            if 'user' in tables or 'users' in tables:
                table_name = 'user' if 'user' in tables else 'users'
                columns = inspector.get_columns(table_name)
                print(f"Columns in {table_name} table:")
                for col in columns:
                    print(f"  - {col['name']} ({col['type']})")

if __name__ == '__main__':
    reset_password()
