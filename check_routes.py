#!/usr/bin/env python3
from app import app

print("📋 Available routes:")
for rule in app.url_map.iter_rules():
    methods = ','.join(rule.methods)
    print(f"  {rule.endpoint:20} {methods:20} {rule.rule}")

print("\n🔍 Checking templates for missing routes...")
import os
for template_file in os.listdir('templates'):
    if template_file.endswith('.html'):
        with open(f'templates/{template_file}', 'r') as f:
            content = f.read()
            import re
            routes = re.findall(r"url_for\('([^']*)'\)", content)
            for route in routes:
                if route not in [rule.endpoint for rule in app.url_map.iter_rules()]:
                    print(f"❌ Missing route: {route} (referenced in {template_file})")
