#!/usr/bin/env python3
"""
Mkweli Dependency Installer
Run this script to install all required dependencies in a virtual environment.
"""

import sys
import subprocess
import os
import venv

def run_command(command, venv_python=None):
    try:
        full_cmd = f"{venv_python} -m {command}" if venv_python else command
        print(f"Running: {full_cmd}")
        subprocess.run(full_cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"Success: {full_cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {command}: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("Mkweli Dependency Installer")
    print("=" * 40)
    
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or later is required.")
        sys.exit(1)
    
    venv_dir = os.path.join(os.path.dirname(__file__), 'venv')
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
    
    if sys.platform == "win32":
        venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
    else:
        venv_python = os.path.join(venv_dir, 'bin', 'python')
    
    if not run_command("pip install --upgrade pip", venv_python=venv_python):
        sys.exit(1)
    
    dependencies = [
        "pip install Flask==2.3.3",
        "pip install Werkzeug==2.3.7",
        "pip install WeasyPrint==58.0",
        "pip install pandas==2.0.3",
        "pip install openpyxl==3.1.2",
        "pip install Jinja2==3.1.2",
        "pip install requests==2.31.0",
        "pip install fuzzywuzzy==0.18.0",
        "pip install bcrypt==4.1.3"
    ]
    
    print("Installing dependencies in virtual environment...")
    for cmd in dependencies:
        if not run_command(cmd, venv_python=venv_python):
            print(f"Failed to install. Run manually in venv: {cmd}")
            sys.exit(1)
    
    print("\nAll dependencies installed successfully!")
    print("\nNext steps (per README):")
    print("1. Activate venv: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)")
    print("2. Download sanctions XML files manually and place in data/ folder (see README for links and renaming)")
    print("3. Run: python init_db.py  # Creates DB and admin user (change password immediately)")
    print("4. Run: python app.py  # Starts the app")
    print("5. Open browser: http://127.0.0.1:5000")
    print("6. Login: admin / securepassword123 (change in Settings)")
    print("7. Go to Sanctions Lists, click 'Update Lists' to load from local files")

if __name__ == "__main__":
    main()
