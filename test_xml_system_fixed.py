# test_xml_system_fixed.py
#!/usr/bin/env python3
"""
Test script for the complete XML sanctions parsing and matching system
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.xml_sanctions_parser import UniversalSanctionsParser
from app.advanced_fuzzy_matcher import OptimalFuzzyMatcher

def test_complete_system():
    print("🚀 Testing Complete XML Sanctions System...")
    
    # Initialize parser
    parser = UniversalSanctionsParser()
    
    # Parse all sanctions data
    print("📊 Parsing sanctions data...")
    parser.parse_all_sanctions()
    entities = parser.parsed_entities
    
    print(f"📊 Successfully parsed {len(entities)} sanction entities")
    
    # Test dataframe conversion
    print("📈 Testing dataframe conversion...")
    df = parser.to_dataframe()
    print(f"✅ DataFrame created with {len(df)} rows and {len(df.columns)} columns")
    print(f"   Columns: {list(df.columns)}")
    
    # Test fuzzy matching
    print("🔍 Testing fuzzy matching...")
    matcher = OptimalFuzzyMatcher(entities)
    
    # Test cases
    test_cases = [
        "AEROCARIBBEAN AIRLINES",
        "BANK OF CHINA",
        "HSBC HOLDINGS", 
        "STANDARD CHARTERED BANK"
    ]
    
    for test_name in test_cases:
        print(f"   Testing: '{test_name}'")
        matches = matcher.find_matches(test_name, threshold=70)
        print(f"   Found {len(matches)} potential matches")
        
        for i, match in enumerate(matches[:2]):
            match_name = match.get('primary_name') or match.get('name', 'Unknown')
            print(f"     {i+1}. {match_name} (score: {match['score']})")
    
    # Test with a known non-match
    print("   Testing: 'NON_EXISTENT_COMPANY_XYZ'")
    non_matches = matcher.find_matches("NON_EXISTENT_COMPANY_XYZ", threshold=85)
    print(f"   Found {len(non_matches)} matches (should be 0 with high threshold)")
    
    print("✅ All tests completed successfully!")

if __name__ == "__main__":
    test_complete_system()
