# check_entity_structure.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.xml_sanctions_parser import UniversalSanctionsParser

def check_entities():
    print("🔍 Checking entity structure...")
    
    parser = UniversalSanctionsParser()
    parser.parse_all_sanctions()
    entities = parser.parsed_entities
    
    if not entities:
        print("❌ No entities loaded")
        return
    
    print(f"📊 Loaded {len(entities)} entities")
    print("\n📋 First entity keys:")
    first_entity = entities[0]
    for key, value in first_entity.items():
        print(f"   - {key}: {value}")
    
    print(f"\n📋 Sample of entity names (first 10):")
    for i, entity in enumerate(entities[:10]):
        # Try different possible name keys
        name = entity.get('name') or entity.get('entity_name') or entity.get('title') or entity.get('full_name') or "No name found"
        print(f"   {i+1}. {name}")

if __name__ == "__main__":
    check_entities()
