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
    
    # Replace import patterns
    replacements = [
        (r'from forms import', 'from .forms import'),
        (r'from models import', 'from .models import'),
        (r'from extensions import', 'from .extensions import'),
        (r'from utils import', 'from .utils import'),
        (r'from app.sanctions_service', 'from .sanctions_service'),
        (r'from database import', 'from .database import'),
        (r'from config import', 'from .config import'),
    ]
    
    original_content = content
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Updated imports in: {filepath}")
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
    'app/config.py'
]

for filepath in files_to_fix:
    fix_imports_in_file(filepath)

print("🎉 Import fixing complete!")
