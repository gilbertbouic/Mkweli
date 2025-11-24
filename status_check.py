#!/usr/bin/env python3
"""
Quick status check for Mkweli
"""
import requests

base_url = "http://localhost:5000"

try:
    # Check if app is running
    response = requests.get(f"{base_url}/sanctions-stats", timeout=5)
    if response.status_code == 200:
        stats = response.json()
        print("✅ Application is running!")
        print(f"📊 Sanctions entities: {stats.get('total_entities', 'N/A')}")
        print(f"📁 Sources: {stats.get('sources', {})}")
    else:
        print(f"❌ Application returned status: {response.status_code}")
        
except Exception as e:
    print(f"❌ Cannot connect to application: {e}")
    print("💡 Make sure the app is running with: python3 app.py")
