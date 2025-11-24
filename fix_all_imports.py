#!/usr/bin/env python3
import os
import re

def fix_imports_in_file(filepath):
    """Fix import paths in a Python file"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    print(f"🔧 Fixing imports in: {filepath}")
    
    # Replace import patterns for app package
    replacements = [
        # Fix module imports to relative
        (r'from routes import', 'from .routes import'),
        (r'from clients import', 'from .clients import'),
        (r'from auth import', 'from .auth import'),
        (r'from models import', 'from .models import'),
        (r'from forms import', 'from .forms import'),
        (r'from extensions import', 'from .extensions import'),
        (r'from utils import', 'from .utils import'),
        (r'from database import', 'from .database import'),
        (r'from config import', 'from .config import'),
        
        # Fix specific function imports
        (r'from routes import login_required', 'from .routes import login_required'),
        (r'from auth import login_required', 'from .routes import login_required'),
        
        # Fix sanctions service imports
        (r'from app.sanctions_service', 'from .sanctions_service'),
        (r'from sanctions_service', 'from .sanctions_service'),
    ]
    
    original_content = content
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Updated imports in: {filepath}")
        
        # Show what changed
        lines_original = original_content.split('\n')
        lines_new = content.split('\n')
        for i, (orig, new_line) in enumerate(zip(lines_original, lines_new)):
            if orig != new_line and 'import' in orig:
                print(f"   Line {i+1}: {orig} -> {new_line}")
    else:
        print(f"✅ No changes needed for: {filepath}")

# Files to fix
files_to_fix = [
    'app/routes.py',
    'app/clients.py', 
    'app/auth.py',
    'app/models.py',
    'app/forms.py',
    'app/extensions.py',
    'app/utils.py',
    'app/database.py',
    'app/config.py',
    'app/__init__.py'
]

for filepath in files_to_fix:
    fix_imports_in_file(filepath)

print("🎉 Import fixing complete!")
