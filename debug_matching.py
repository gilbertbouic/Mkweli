# debug_matching.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.xml_sanctions_parser import UniversalSanctionsParser
from app.advanced_fuzzy_matcher import OptimalFuzzyMatcher

def test_matching():
    print("🔍 Testing matching system...")
    
    # Load sanctions data
    parser = UniversalSanctionsParser()
    parser.parse_all_sanctions()
    entities = parser.parsed_entities
    print(f"📊 Loaded {len(entities)} entities")
    
    # Test with known entities that should match
    test_cases = [
        "AEROCARIBBEAN AIRLINES",
        "BANK OF CHINA", 
        "HSBC",
        "STANDARD CHARTERED"
    ]
    
    matcher = OptimalFuzzyMatcher(entities)
    
    for test_name in test_cases:
        print(f"\n🔍 Testing: '{test_name}'")
        matches = matcher.find_matches(test_name, threshold=70)
        print(f"   Found {len(matches)} matches")
        
        for match in matches[:3]:  # Show top 3 matches
            match_name = match.get('primary_name') or match.get('name', 'No name')
            print(f"   - '{match_name}' (score: {match['score']})")
    
    # Also test with a name that should definitely be in the list
    print(f"\n📋 Sample of loaded names (first 10):")
    for i, entity in enumerate(entities[:10]):
        entity_name = entity.get('primary_name', 'No primary name')
        print(f"   {i+1}. {entity_name}")

if __name__ == "__main__":
    test_matching()
