#!/usr/bin/env python3
"""
Simple test for the sanctions system
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

def simple_test():
    print("🔍 Simple System Test")
    
    try:
        # Test direct imports from the app directory
        sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
        
        # Import directly from the files
        from robust_sanctions_parser import RobustSanctionsParser
        from advanced_fuzzy_matcher import OptimalFuzzyMatcher
        print("✅ All imports successful")
        
        # Test parsing
        parser = RobustSanctionsParser()
        entities = parser.parse_all_sanctions()
        print(f"📊 Parsed {len(entities)} entities")
        
        if entities:
            # Test matching
            matcher = OptimalFuzzyMatcher(entities)
            
            # Test AEROCARIBBEAN AIRLINES
            test_name = "AEROCARIBBEAN AIRLINES"
            matches = matcher.find_matches(test_name, threshold=80)
            print(f"🔍 '{test_name}': {len(matches)} matches")
            
            for match in matches:
                print(f"   - {match['primary_name']} (score: {match['score']}, source: {match['source']})")
            
            # Show stats
            stats = matcher.get_matching_stats()
            print(f"📈 Clean entities: {stats['clean_entities']}")
            print(f"🗑️  Garbage removed: {stats['garbage_removed']}")
            
        else:
            print("❌ No entities parsed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_test()
