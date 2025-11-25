# test_improved_system.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.universal_sanctions_parser import UniversalSanctionsParser
from app.advanced_fuzzy_matcher import OptimalFuzzyMatcher

def test_improved_system():
    print("🔍 Testing Improved Sanctions System...")
    
    # Load with new parser
    parser = UniversalSanctionsParser()
    entities = parser.parse_all_sanctions()
    
    print(f"📊 Total entities: {len(entities)}")
    
    # Test matching
    matcher = OptimalFuzzyMatcher(entities)
    stats = matcher.get_matching_stats()
    print(f"✅ Clean entities: {stats['clean_entities']}")
    print(f"🚮 Garbage removed: {stats['garbage_removed']}")
    
    # Test cases
    test_cases = ["AEROCARIBBEAN AIRLINES", "BANK OF CHINA", "HSBC"]
    
    for test_name in test_cases:
        print(f"\n🔍 Testing: '{test_name}'")
        matches = matcher.find_matches(test_name, threshold=70)
        print(f"   Found {len(matches)} clean matches")
        
        for match in matches[:3]:
            print(f"   - '{match['primary_name']}' (score: {match['score']}, source: {match['source']})")

if __name__ == "__main__":
    test_improved_system()
