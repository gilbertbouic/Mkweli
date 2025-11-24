#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.xml_sanctions_parser import UniversalSanctionsParser
from app.advanced_fuzzy_matcher import OptimalFuzzyMatcher
import pandas as pd

def test_complete_system():
    print("🚀 Testing Complete XML Sanctions System...")
    
    # Parse all XML sanctions
    parser = UniversalSanctionsParser()
    sanctions_entities = parser.parse_all_sanctions('data')
    
    print(f"📊 Successfully parsed {len(sanctions_entities)} sanction entities")
    
    if not sanctions_entities:
        print("❌ No sanctions entities parsed. Check XML files.")
        return
    
    # Convert to DataFrame for inspection
    df = parser.to_dataframe()
    print(f"📋 Created DataFrame with {len(df)} name entries")
    
    if len(df) > 0:
        print("\n📈 Sample of parsed data:")
        print(df.head(10))
        
        print("\n📊 Summary by source:")
        print(df['source'].value_counts())
    
    # Initialize fuzzy matcher
    matcher = OptimalFuzzyMatcher(sanctions_entities)
    stats = matcher.get_matching_stats()
    print(f"\n📊 Matching System Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test matching with different scenarios
    test_cases = [
        {"name": "Example Corporation", "type": "company"},
        {"name": "John Smith", "type": "individual"},
        {"name": "ACME Ltd", "type": "company"},
        {"name": "Maria Rodriguez", "type": "individual"},
        {"name": "Global Trading Group", "type": "company"},
    ]
    
    print("\n🧪 Testing Fuzzy Matching:")
    
    # Test individual strategies
    for test_case in test_cases:
        print(f"\n🔍 Searching: '{test_case['name']}' ({test_case['type']})")
        
        # Test optimal strategy
        matches = matcher.match_single_name(
            test_case['name'], 
            threshold=80, 
            strategy='optimal'
        )
        
        print(f"   Optimal strategy matches: {len(matches)}")
        for match in matches[:2]:  # Show top 2 matches
            print(f"     - {match['matched_name']} (Score: {match['score']:.1f})")
            print(f"       Source: {match['entity']['source']}")
    
    # Test batch screening
    print(f"\n🎯 Testing Batch Screening:")
    batch_results = matcher.batch_screen_entities(test_cases, threshold=80)
    
    for entity_name, result in batch_results.items():
        print(f"   {entity_name}: {len(result['matches'])} matches ({result['strategy_used']} strategy)")

if __name__ == '__main__':
    test_complete_system()
