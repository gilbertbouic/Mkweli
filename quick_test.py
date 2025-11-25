# quick_test.py
import sys
import os

# Add the app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from sanctions_loader import SanctionsLoader
    from advanced_fuzzy_matcher import OptimalFuzzyMatcher
    
    print("🚀 Testing components...")
    
    # Test loader
    loader = SanctionsLoader()
    data = loader.load_sanctions_data()
    print(f"📊 Loaded {len(data)} entities")
    
    # Test matcher
    if data:
        matcher = OptimalFuzzyMatcher(data)
        test_name = "AEROCARIBBEAN AIRLINES"
        matches = matcher.find_matches(test_name)
        print(f"🔍 Testing '{test_name}': Found {len(matches)} matches")
        
        for match in matches[:3]:  # Show first 3 matches
            print(f"   - {match['name']} (score: {match['score']})")
    
    print("✅ All components working!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Try: pip install thefuzz python-levenshtein")
except Exception as e:
    print(f"❌ Error: {e}")
