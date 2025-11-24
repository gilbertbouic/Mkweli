#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.sanctions_loader import SanctionsLoader
from app.fuzzy_matcher import AdvancedFuzzyMatcher, EnhancedFuzzyMatcher

def test_system():
    print("🚀 Testing Sanctions System...")
    
    # Load sanctions
    loader = SanctionsLoader('data')
    sanctions = loader.load_all_sanctions()
    
    print(f"📊 Loaded {len(sanctions)} sanction entities")
    
    if not sanctions:
        print("❌ No sanctions loaded. Check data files.")
        return
    
    # Test matching
    test_names = [
        "Example Corporation",
        "John Smith",
        "ACME Ltd",
        "Test Company GmbH"
    ]
    
    print("\n🧪 Testing Basic Fuzzy Matching:")
    basic_matcher = AdvancedFuzzyMatcher(sanctions)
    
    for name in test_names:
        matches = basic_matcher.match_entity(name, threshold=70)
        print(f"\nSearch: '{name}'")
        print(f"Matches found: {len(matches)}")
        for match in matches[:3]:  # Show top 3
            print(f"  - {match['entity'].get('name')} (Score: {match['score']:.1f})")
    
    print("\n🧪 Testing Enhanced Fuzzy Matching:")
    enhanced_matcher = EnhancedFuzzyMatcher(sanctions)
    
    for name in test_names:
        matches = enhanced_matcher.match_entity_enhanced(name, threshold=70)
        print(f"\nSearch: '{name}'")
        print(f"Matches found: {len(matches)}")
        for match in matches[:3]:
            print(f"  - {match['entity'].get('name')} (Score: {match['score']:.1f})")

if __name__ == '__main__':
    test_system()
