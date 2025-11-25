# test_robust_system.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.robust_sanctions_parser import RobustSanctionsParser
from app.advanced_fuzzy_matcher import OptimalFuzzyMatcher

def test_robust_system():
    print("🔍 Testing Robust Sanctions System...")
    
    # Load with robust parser
    parser = RobustSanctionsParser()
    entities = parser.parse_all_sanctions()
    
    print(f"📊 Total entities: {len(entities)}")
    
    if not entities:
        print("❌ No entities parsed. Checking data files...")
        # List data files
        data_dir = "data"
        if os.path.exists(data_dir):
            files = os.listdir(data_dir)
            print(f"📁 Data files: {files}")
        return
    
    # Show sample entities
    print(f"\n📋 Sample entities (first 10):")
    for i, entity in enumerate(entities[:10]):
        print(f"   {i+1}. {entity.get('primary_name', 'No name')} ({entity.get('list_type', 'Unknown')})")
    
    # Test matching
    matcher = OptimalFuzzyMatcher(entities)
    stats = matcher.get_matching_stats()
    print(f"\n✅ Clean entities: {stats['clean_entities']}")
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
        matches = matcher.find_matches(test_name, threshold=70)
        print(f"   Found {len(matches)} matches")
        
        for match in matches[:5]:
            print(f"   - '{match['primary_name']}' (score: {match['score']}, source: {match['source']})")
        
        if not matches:
            print("   ⚠️  No good matches found")

if __name__ == "__main__":
    test_robust_system()
