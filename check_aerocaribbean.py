# check_aerocaribbean.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.xml_sanctions_parser import UniversalSanctionsParser

def check_aerocaribbean():
    print("🔍 Specifically checking for AEROCARIBBEAN AIRLINES...")
    
    parser = UniversalSanctionsParser()
    parser.parse_all_sanctions()
    entities = parser.parsed_entities
    
    # Search for any airline or Caribbean entities
    airline_entities = []
    for entity in entities:
        primary_name = entity.get('primary_name', '').upper()
        if 'AIRLINE' in primary_name or 'AIRWAYS' in primary_name or 'AVIATION' in primary_name:
            airline_entities.append(entity)
        elif 'CARIBBEAN' in primary_name:
            airline_entities.append(entity)
    
    print(f"📋 Found {len(airline_entities)} airline/Caribbean related entities:")
    for i, entity in enumerate(airline_entities[:20]):
        primary_name = entity.get('primary_name', 'No name')
        list_type = entity.get('list_type', 'Unknown')
        print(f"   {i+1}. {primary_name} - {list_type}")
    
    # Also check if there are any exact matches
    exact_matches = [e for e in entities if 'AEROCARIBBEAN' in e.get('primary_name', '').upper()]
    print(f"\n🎯 Exact AEROCARIBBEAN matches: {len(exact_matches)}")
    for match in exact_matches:
        print(f"   - {match.get('primary_name')}")

if __name__ == "__main__":
    check_aerocaribbean()
