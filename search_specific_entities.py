# search_specific_entities.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.xml_sanctions_parser import UniversalSanctionsParser
from app.advanced_fuzzy_matcher import OptimalFuzzyMatcher

def search_specific_entities():
    print("🔍 Searching for specific entities in sanctions lists...")
    
    # Load sanctions data
    parser = UniversalSanctionsParser()
    parser.parse_all_sanctions()
    entities = parser.parsed_entities
    print(f"📊 Loaded {len(entities)} entities")
    
    # Search for entities that might contain our test names
    search_terms = ["AEROCARIBBEAN", "CARIBBEAN", "AIRLINE", "BANK", "CHINA", "HSBC", "STANDARD", "CHARTERED"]
    
    found_entities = []
    for term in search_terms:
        for entity in entities:
            primary_name = entity.get('primary_name', '').upper()
            if term.upper() in primary_name:
                found_entities.append(entity)
                if len(found_entities) >= 20:  # Limit to 20 examples
                    break
        if len(found_entities) >= 20:
            break
    
    print(f"\n📋 Found {len(found_entities)} entities containing search terms:")
    for i, entity in enumerate(found_entities[:15]):
        primary_name = entity.get('primary_name', 'No name')
        entity_type = entity.get('type', 'Unknown')
        list_type = entity.get('list_type', 'Unknown')
        print(f"   {i+1}. {primary_name} ({entity_type}) - {list_type}")
    
    # Now test fuzzy matching
    print(f"\n🎯 Testing fuzzy matching...")
    matcher = OptimalFuzzyMatcher(entities)
    
    test_cases = [
        "AEROCARIBBEAN AIRLINES",
        "BANK OF CHINA", 
        "HSBC",
        "STANDARD CHARTERED"
    ]
    
    for test_name in test_cases:
        print(f"\n🔍 Testing: '{test_name}'")
        matches = matcher.find_matches(test_name, threshold=70)
        print(f"   Found {len(matches)} matches")
        
        for match in matches[:5]:  # Show top 5 matches
            match_name = match.get('primary_name') or match.get('name', 'No name')
            score = match.get('score', 0)
            source = match.get('source', 'Unknown')
            print(f"   - '{match_name}' (score: {score}, source: {source})")

if __name__ == "__main__":
    search_specific_entities()
