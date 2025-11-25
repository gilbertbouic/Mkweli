# test_improved_matching.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.robust_sanctions_parser import RobustSanctionsParser
from app.advanced_fuzzy_matcher import OptimalFuzzyMatcher

def test_improved_matching():
    print("🔍 Testing Improved Matching...")
    
    # Load with robust parser
    parser = RobustSanctionsParser()
    entities = parser.parse_all_sanctions()
    
    print(f"📊 Total entities: {len(entities)}")
    
    # Test matching with better filtering
    matcher = OptimalFuzzyMatcher(entities)
    stats = matcher.get_matching_stats()
    print(f"✅ Clean entities: {stats['clean_entities']}")
    print(f"🚮 Garbage removed: {stats['garbage_removed']}")
    
    # Test specific known entities
    test_cases = [
        "AEROCARIBBEAN AIRLINES",
        "BANK OF CHINA", 
        "HSBC",
        "STANDARD CHARTERED"
    ]
    
    for test_name in test_cases:
        print(f"\n🎯 Testing: '{test_name}'")
        matches = matcher.find_matches(test_name, threshold=80)  # Higher threshold
        print(f"   Found {len(matches)} quality matches")
        
        for match in matches:
            print(f"   - '{match['primary_name']}' (score: {match['score']}, source: {match['source']})")
        
        if not matches:
            print("   ⚠️  No good matches found")

if __name__ == "__main__":
    test_improved_matching()
