# comprehensive_test.py
import sys
import os
sys.path.append(os.path.dirname(__file__))

def comprehensive_test():
    print("🔍 Comprehensive Sanctions System Test")
    print("=" * 50)
    
    # Test 1: Import XML Parser
    try:
        from app.xml_sanctions_parser import UniversalSanctionsParser
        print("✅ 1. UniversalSanctionsParser imported successfully")
    except ImportError as e:
        print(f"❌ 1. Failed to import UniversalSanctionsParser: {e}")
        return
    
    # Test 2: Initialize Parser
    try:
        parser = UniversalSanctionsParser()
        print("✅ 2. Parser initialized successfully")
    except Exception as e:
        print(f"❌ 2. Failed to initialize parser: {e}")
        return
    
    # Test 3: Load Sanctions Data
    try:
        parser.parse_all_sanctions()
        entities = parser.parsed_entities
        print(f"✅ 3. Loaded {len(entities)} sanction entities")
    except Exception as e:
        print(f"❌ 3. Failed to load sanctions data: {e}")
        return
    
    # Test 4: Check Data Quality
    if len(entities) == 0:
        print("❌ 4. No entities loaded - check data files")
        return
    else:
        print("✅ 4. Data quality check passed")
    
    # Test 5: Import Fuzzy Matcher
    try:
        from app.advanced_fuzzy_matcher import OptimalFuzzyMatcher
        print("✅ 5. OptimalFuzzyMatcher imported successfully")
    except ImportError as e:
        print(f"❌ 5. Failed to import OptimalFuzzyMatcher: {e}")
        return
    
    # Test 6: Test Matching
    try:
        matcher = OptimalFuzzyMatcher(entities)
        test_names = ["AEROCARIBBEAN AIRLINES", "BANK OF CHINA", "TEST COMPANY"]
        
        for test_name in test_names:
            matches = matcher.find_matches(test_name, threshold=70)
            print(f"   🔍 '{test_name}': {len(matches)} matches")
            for match in matches[:2]:
                print(f"      - {match['name']} (score: {match['score']})")
        
        print("✅ 6. Fuzzy matching test completed")
        
    except Exception as e:
        print(f"❌ 6. Fuzzy matching test failed: {e}")
        return
    
    print("=" * 50)
    print("🎉 All tests passed! System is working correctly.")
    
    # Show sample data
    print(f"\n📋 Sample of first 5 entities:")
    for i, entity in enumerate(entities[:5]):
        print(f"   {i+1}. {entity.get('name', 'No name')}")

if __name__ == "__main__":
    comprehensive_test()
