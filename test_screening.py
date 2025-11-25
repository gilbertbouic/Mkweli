#!/usr/bin/env python3
"""
Test the sanctions screening endpoint
"""
import requests
import json

def test_screening():
    print("🔍 Testing Screening Endpoint...")
    
    # Test data
    test_cases = [
        {"client_name": "AEROCARIBBEAN AIRLINES", "client_type": "Company"},
        {"client_name": "BANK OF CHINA", "client_type": "Company"},
        {"client_name": "TEST COMPANY", "client_type": "Company"}
    ]
    
    for test_data in test_cases:
        try:
            response = requests.post(
                'http://localhost:5000/check_sanctions',
                data=test_data
            )
            
            print(f"\n🎯 Testing: '{test_data['client_name']}'")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Matches found: {result['matches_found']}")
                for match in result['matches']:
                    print(f"      - {match['primary_name']} (score: {match['score']})")
            else:
                print(f"   ❌ Error: {response.json()}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")

if __name__ == "__main__":
    # First make sure the server is running, then run this test
    print("Make sure the Flask app is running on http://localhost:5000")
    input("Press Enter to run the test...")
    test_screening()
