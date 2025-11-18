#!/usr/bin/env python3
"""
MkweliAML Dependency Installer
Run this script to install all required dependencies
"""

import sys
import subprocess
import os

def run_command(command):
    try:
        print(f"Running: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"Success: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {command}: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("MkweliAML Dependency Installer")
    print("=" * 40)
    
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or later is required.")
        sys.exit(1)
    
    dependencies = [
        "pip install Flask==2.3.3",
        "pip install Werkzeug==2.3.7", 
        "pip install WeasyPrint==58.0",
        "pip install pandas==2.0.3",
        "pip install openpyxl==3.1.2",
        "pip install Jinja2==3.1.2",
        "pip install requests==2.31.0",
        "pip install fuzzywuzzy==0.18.0"
    ]
    
    print("Installing dependencies...")
    for cmd in dependencies:
        if not run_command(cmd):
            print(f"Failed to install. Run manually: {cmd}")
            sys.exit(1)
    
    print("\nAll dependencies installed successfully!")
    print("\nNext: Run python init_db.py, then python app.py")

if __name__ == "__main__":
    main()
