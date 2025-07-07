#!/usr/bin/env python3
"""
Quick test script to verify the app is working
"""

import requests
import sys

def test_app():
    """Test if the Flask app is running"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Simple eBay Dropshipping App...")
    print("-" * 40)
    
    # Test 1: Home page
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Home page is working")
        else:
            print(f"❌ Home page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to app. Make sure it's running with: python app.py")
        print(f"   Error: {e}")
        sys.exit(1)
    
    # Test 2: API Health
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health check: {data['status']}")
        else:
            print(f"❌ API Health failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API Health error: {e}")
    
    # Test 3: Search API
    try:
        response = requests.post(f"{base_url}/api/search", 
                                json={"keyword": "laptop"})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search API working: Found {len(data['results'])} results")
        else:
            print(f"❌ Search API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Search API error: {e}")
    
    print("-" * 40)
    print("🎉 Testing complete!")

if __name__ == "__main__":
    test_app() 