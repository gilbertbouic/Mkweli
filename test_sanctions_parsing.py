#!/usr/bin/env python3
"""Test script to verify sanctions parsing improvements"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.sanctions_service import init_sanctions_service, get_sanctions_stats

def main():
    print("🧪 Testing improved sanctions parsing...")
    
    # Clear any existing cache
    cache_file = "instance/sanctions_cache.pkl"
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print("🗑️  Cleared existing cache")
    
    # Initialize service
    result = init_sanctions_service()
    print(f"✅ {result}")
    
    # Get detailed stats
    stats = get_sanctions_stats()
    print("\n📊 Parsing Results:")
    print(f"   Total entities: {stats['total_entities']}")
    
    print("\n📋 By Source:")
    for source, count in stats['sources'].items():
        print(f"   {source}: {count} entities")
    
    print(f"\n📅 Last loaded: {stats['last_loaded']}")

if __name__ == "__main__":
    main()
