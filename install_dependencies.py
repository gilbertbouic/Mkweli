#!/usr/bin/env python3
"""
MkweliAML Dependency Installer
<<<<<<< HEAD
Run this script to install all required dependencies
=======
Run this script to install all required dependencies in a virtual environment.
>>>>>>> 4bfb9585fdcb6db813b32955452182091acac196
"""

import sys
import subprocess
import os
<<<<<<< HEAD

def run_command(command):
    try:
        print(f"Running: {command}")
=======
import venv

def run_command(command, venv_python=None):
    """Run a shell command and return success status"""
    try:
        print(f"Running: {command}")
        if venv_python:
            command = f"{venv_python} -m {command}"
>>>>>>> 4bfb9585fdcb6db813b32955452182091acac196
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
    
<<<<<<< HEAD
=======
    # Check Python version
>>>>>>> 4bfb9585fdcb6db813b32955452182091acac196
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or later is required.")
        sys.exit(1)
    
<<<<<<< HEAD
    dependencies = [
        "pip install Flask==2.3.3",
        "pip install Werkzeug==2.3.7", 
=======
    # Create virtual environment if not exists
    venv_dir = os.path.join(os.path.dirname(__file__), 'venv')
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
    
    # Get venv Python path (cross-platform)
    if sys.platform == "win32":
        venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
    else:
        venv_python = os.path.join(venv_dir, 'bin', 'python')
    
    # Upgrade pip in venv
    run_command("pip install --upgrade pip", venv_python=venv_python)
    
    # Install dependencies in venv
    dependencies = [
        "pip install Flask==2.3.3",
        "pip install Werkzeug==2.3.7",
>>>>>>> 4bfb9585fdcb6db813b32955452182091acac196
        "pip install WeasyPrint==58.0",
        "pip install pandas==2.0.3",
        "pip install openpyxl==3.1.2",
        "pip install Jinja2==3.1.2",
<<<<<<< HEAD
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
=======
        "pip install bcrypt==4.1.3"
    ]
    
    print("Installing dependencies in virtual environment...")
    for cmd in dependencies:
        if not run_command(cmd, venv_python=venv_python):
            print(f"Failed to install dependencies. Please run manually: {cmd}")
            sys.exit(1)
    
    print("\nAll dependencies installed successfully!")
    print("\nNext steps:")
    print("1. Run the app using the platform-specific script (run_windows.bat or run_linux.sh)")
    print("2. Open browser to: http://localhost:5000")
    print("3. Set up your master password on first launch")
    print("4. Start using MkweliAML!")
>>>>>>> 4bfb9585fdcb6db813b32955452182091acac196

if __name__ == "__main__":
    main()
