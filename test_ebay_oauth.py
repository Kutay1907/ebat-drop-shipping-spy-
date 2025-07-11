#!/usr/bin/env python3
"""
Test script for eBay OAuth 2.0 implementation.
Run this to verify your OAuth setup is working correctly.
"""

import os
import asyncio
import httpx
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your deployment URL
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_REDIRECT_URI = os.getenv("EBAY_REDIRECT_URI")

async def test_oauth_configuration():
    """Test if OAuth is properly configured."""
    print("=" * 60)
    print("Testing eBay OAuth Configuration")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test debug endpoint
        response = await client.get(f"{BASE_URL}/debug/oauth-url")
        data = response.json()
        
        print("\n1. Environment Check:")
        for key, value in data.get("environment_check", {}).items():
            status = "✅" if value == "SET" else "❌"
            print(f"   {status} {key}: {value}")
        
        if data.get("status") == "success":
            print(f"\n2. OAuth URL Generated Successfully")
            print(f"   URL Length: {data.get('url_length')} characters")
            print(f"   Scopes Count: {data.get('scopes_count')}")
            
            # Parse the generated URL
            parsed = urlparse(data.get("generated_url", ""))
            params = parse_qs(parsed.query)
            
            print(f"\n3. OAuth Parameters:")
            print(f"   Client ID: {params.get('client_id', ['Not found'])[0][:20]}...")
            print(f"   Response Type: {params.get('response_type', ['Not found'])[0]}")
            print(f"   Redirect URI: {params.get('redirect_uri', ['Not found'])[0]}")
            print(f"   Scopes: {len(params.get('scope', [''])[0].split())}")
        else:
            print(f"\n❌ Error: {data.get('error')}")

async def test_auth_endpoints():
    """Test authentication endpoints."""
    print("\n" + "=" * 60)
    print("Testing Authentication Endpoints")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test connect endpoint
        response = await client.get(f"{BASE_URL}/connect/ebay", follow_redirects=False)
        print(f"\n1. GET /connect/ebay")
        print(f"   Status: {response.status_code}")
        if response.status_code == 307:
            location = response.headers.get("location", "")
            print(f"   ✅ Redirects to eBay OAuth")
            print(f"   Location: {location[:100]}...")
        else:
            print(f"   ❌ Expected redirect, got {response.status_code}")
        
        # Test status endpoint
        response = await client.get(f"{BASE_URL}/auth/ebay/status")
        print(f"\n2. GET /auth/ebay/status")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Connected: {data.get('is_connected', False)}")
        print(f"   Message: {data.get('message', 'No message')}")

async def test_api_endpoints():
    """Test eBay API endpoints (requires authentication)."""
    print("\n" + "=" * 60)
    print("Testing eBay API Endpoints")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        endpoints = [
            "/api/ebay/inventory",
            "/api/ebay/orders",
            "/ebay/profile"
        ]
        
        for endpoint in endpoints:
            response = await client.get(f"{BASE_URL}{endpoint}")
            print(f"\n{endpoint}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 401:
                print(f"   ✅ Correctly requires authentication")
            else:
                data = response.json()
                print(f"   Response: {data}")

def print_setup_instructions():
    """Print setup instructions if configuration is missing."""
    print("\n" + "=" * 60)
    print("Setup Instructions")
    print("=" * 60)
    print("\n1. Set up environment variables:")
    print("   EBAY_CLIENT_ID=your-app-id")
    print("   EBAY_CLIENT_SECRET=your-cert-id")
    print("   EBAY_REDIRECT_URI=your-runame")
    print("   ENCRYPTION_KEY=your-32-char-key")
    print("\n2. Configure RuName in eBay Developer Console:")
    print("   - Auth Accepted URL: https://your-app.com/auth/ebay/callback")
    print("   - Auth Declined URL: https://your-app.com/?auth_status=declined")
    print("\n3. Run the application:")
    print("   uvicorn app.main:app --reload")

async def main():
    """Run all tests."""
    print("🚀 eBay OAuth 2.0 Test Suite")
    print("=" * 60)
    
    # Check if environment variables are set
    if not all([EBAY_CLIENT_ID, EBAY_REDIRECT_URI]):
        print("❌ Missing environment variables!")
        print_setup_instructions()
        return
    
    try:
        await test_oauth_configuration()
        await test_auth_endpoints()
        await test_api_endpoints()
        
        print("\n" + "=" * 60)
        print("✅ Test suite completed!")
        print("\nNext steps:")
        print("1. Visit http://localhost:8000/connect/ebay to test the full flow")
        print("2. After authentication, test the API endpoints again")
        print("3. Check http://localhost:8000/docs for interactive API documentation")
        
    except httpx.ConnectError:
        print("\n❌ Could not connect to the application!")
        print("Make sure the application is running on", BASE_URL)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 