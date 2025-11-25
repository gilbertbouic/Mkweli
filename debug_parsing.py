# debug_parsing.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.universal_sanctions_parser import UniversalSanctionsParser

def debug_parsing():
    print("🔍 Debugging XML Parsing...")
    
    parser = UniversalSanctionsParser()
    entities = parser.parse_all_sanctions()
    
    print(f"📊 Total entities parsed: {len(entities)}")
    
    # Show entities by source
    sources = {}
    for entity in entities:
        source = entity.get('source', 'unknown')
        if source not in sources:
            sources[source] = []
        sources[source].append(entity)
    
    for source, entities_list in sources.items():
        print(f"\n📁 {source}: {len(entities_list)} entities")
        for entity in entities_list[:5]:  # Show first 5 per source
            print(f"   - {entity.get('primary_name', 'No name')}")
    
    # Check if we have any airline-related entities
    print(f"\n🎯 Searching for airline-related entities:")
    airline_entities = []
    for entity in entities:
        name = entity.get('primary_name', '').upper()
        if 'AIRLINE' in name or 'AIRWAYS' in name or 'AVIATION' in name or 'AERO' in name:
            airline_entities.append(entity)
    
    print(f"   Found {len(airline_entities)} airline-related entities:")
    for entity in airline_entities[:10]:
        print(f"   - {entity.get('primary_name')} (source: {entity.get('source')})")

if __name__ == "__main__":
    debug_parsing()
