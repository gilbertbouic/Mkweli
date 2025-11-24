#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.sanctions_service import init_sanctions_service, screen_entity, batch_screen_entities, get_sanctions_stats

def test_screening():
    print("🚀 Testing Client Screening System...")
    
    # Initialize service
    init_msg = init_sanctions_service()
    print(f"✅ {init_msg}")
    
    # Show stats
    stats = get_sanctions_stats()
    print(f"📊 Sanctions Stats:")
    print(f"   Total entities: {stats['total_entities']}")
    print(f"   Last loaded: {stats['last_loaded']}")
    print(f"   Sources: {stats['sources']}")
    
    # Test cases with different entity types
    test_cases = [
        {"name": "Example Corporation", "type": "company"},
        {"name": "John Smith", "type": "individual"},
        {"name": "HAJI KHAIRULLAH", "type": "individual"},
        {"name": "AEROCARIBBEAN AIRLINES", "type": "company"},
        {"name": "ROSHAN MONEY EXCHANGE", "type": "company"},
        {"name": "Maria Rodriguez", "type": "individual"},
        {"name": "Global Trading Group", "type": "company"},
    ]
    
    print(f"\n🧪 Screening {len(test_cases)} test clients...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Client: '{test_case['name']}' ({test_case['type']})")
        
        matches = screen_entity(test_case['name'], test_case['type'], threshold=80)
        
        if matches:
            print(f"   ⚠️  {len(matches)} potential matches found:")
            for match in matches[:2]:  # Show top 2 matches
                print(f"      - {match['matched_name']} (Score: {match['score']:.1f})")
                print(f"        Source: {match['entity']['source']} | Type: {match['entity'].get('type', 'unknown')}")
        else:
            print(f"   ✅ No matches found")
    
    # Test batch screening
    print(f"\n🎯 Testing Batch Screening:")
    batch_results = batch_screen_entities(test_cases, threshold=80)
    
    print(f"   Searched: {batch_results['total_searched']} clients")
    print(f"   Matches found for: {batch_results['matches_found']} clients")

if __name__ == '__main__':
    test_screening()
