#!/usr/bin/env python3
"""
🔍 eBay Authentication Diagnostic Script
=======================================

This script will help you diagnose authentication issues with your eBay API integration.
Run this script both locally and on Railway to identify the problem.

Usage:
    python debug_auth.py

The script will:
1. Check environment variables
2. Test eBay token request
3. Verify API connectivity
4. Provide specific troubleshooting steps
"""

import os
import asyncio
import json
import sys
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import httpx
try:
    import httpx
except ImportError:
    print("❌ ERROR: httpx is not installed. Install it with: pip install httpx")
    sys.exit(1)

class EbayAuthDebugger:
    """Comprehensive eBay authentication debugger."""
    
    def __init__(self):
        self.client_id = os.getenv("EBAY_CLIENT_ID")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET")
        self.oauth_token = os.getenv("EBAY_OAUTH_TOKEN") or os.getenv("EBAY_USER_TOKEN")
        
    def print_section(self, title: str):
        """Print a formatted section header."""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def check_environment_variables(self):
        """Check if required environment variables are set."""
        self.print_section("Environment Variables Check")
        
        variables_to_check = [
            ("EBAY_CLIENT_ID", self.client_id),
            ("EBAY_CLIENT_SECRET", self.client_secret),
            ("EBAY_OAUTH_TOKEN", self.oauth_token),
            ("EBAY_USER_TOKEN", os.getenv("EBAY_USER_TOKEN")),
            ("PORT", os.getenv("PORT")),
        ]
        
        for var_name, value in variables_to_check:
            if value:
                # Show first 4 and last 4 characters for security
                if len(value) > 8:
                    masked_value = f"{value[:4]}...{value[-4:]}"
                else:
                    masked_value = f"{value[:2]}..."
                print(f"✅ {var_name}: {masked_value}")
            else:
                print(f"❌ {var_name}: NOT SET")
        
        # Check if we have minimum required variables
        if not self.client_id or not self.client_secret:
            print(f"\n❌ CRITICAL: Missing required eBay credentials!")
            print(f"   You need to set both EBAY_CLIENT_ID and EBAY_CLIENT_SECRET")
            print(f"   in your Railway environment variables.")
            return False
        
        print(f"\n✅ Required environment variables are set!")
        return True
    
    async def test_token_request(self):
        """Test requesting a token directly from eBay."""
        self.print_section("eBay Token Request Test")
        
        if not self.client_id or not self.client_secret:
            print("❌ Cannot test token request: Missing credentials")
            return None
        
        # Prepare the request
        import base64
        credentials = f"{self.client_id}:{self.client_secret}"
        auth_header = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_header}"
        }
        
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
        
        token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        
        try:
            print(f"🔄 Requesting token from: {token_url}")
            print(f"🔄 Using Client ID: {self.client_id[:4]}...{self.client_id[-4:]}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(token_url, headers=headers, data=data)
            
            print(f"📡 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                print(f"✅ Token request successful!")
                print(f"   Token type: {token_data.get('token_type')}")
                print(f"   Expires in: {token_data.get('expires_in')} seconds")
                print(f"   Access token: {token_data.get('access_token', '')[:15]}...")
                return token_data.get('access_token')
            else:
                print(f"❌ Token request failed!")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
                # Common error explanations
                if response.status_code == 400:
                    print(f"\n💡 Error 400 usually means:")
                    print(f"   - Invalid client credentials")
                    print(f"   - Wrong scope or grant_type")
                    print(f"   - Malformed request")
                elif response.status_code == 401:
                    print(f"\n💡 Error 401 usually means:")
                    print(f"   - Invalid EBAY_CLIENT_ID or EBAY_CLIENT_SECRET")
                    print(f"   - Credentials don't match any eBay app")
                elif response.status_code == 403:
                    print(f"\n💡 Error 403 usually means:")
                    print(f"   - App not approved for production")
                    print(f"   - Insufficient permissions")
                
                return None
                
        except Exception as e:
            print(f"❌ Exception during token request: {e}")
            return None
    
    async def test_api_call(self, token: str):
        """Test making an API call with the token."""
        self.print_section("eBay API Call Test")
        
        if not token:
            print("❌ Cannot test API call: No token available")
            return False
        
        # Test with a simple product search
        api_url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "Accept": "application/json"
        }
        
        params = {
            "q": "test",
            "limit": 1
        }
        
        try:
            print(f"🔄 Testing API call to: {api_url}")
            print(f"🔄 Using token: {token[:15]}...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_url, headers=headers, params=params)
            
            print(f"📡 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                total_results = data.get("total", 0)
                print(f"✅ API call successful!")
                print(f"   Search results found: {total_results}")
                print(f"   Items returned: {len(data.get('itemSummaries', []))}")
                return True
            else:
                print(f"❌ API call failed!")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during API call: {e}")
            return False
    
    async def check_app_client_integration(self):
        """Check if the app's eBay client works."""
        self.print_section("App Integration Test")
        
        try:
            # Try to import the app's eBay client
            from app.ebay_api_client import ebay_client
            
            print("✅ Successfully imported ebay_client")
            
            # Test connection
            print("🔄 Testing app's eBay client connection...")
            
            connection_result = await ebay_client.test_connection()
            
            print(f"📊 Connection test results:")
            print(f"   Overall status: {connection_result.get('overall_status')}")
            
            for test in connection_result.get('tests', []):
                status_emoji = "✅" if test['status'] == 'success' else "❌"
                print(f"   {status_emoji} {test['test']}: {test['message']}")
            
            return connection_result.get('overall_status') == 'healthy'
            
        except ImportError as e:
            print(f"❌ Cannot import app's eBay client: {e}")
            print(f"   This might be normal if running outside the app directory")
            return False
        except Exception as e:
            print(f"❌ Error testing app integration: {e}")
            return False
    
    def provide_troubleshooting_steps(self, token_success: bool, api_success: bool):
        """Provide specific troubleshooting steps based on test results."""
        self.print_section("Troubleshooting Steps")
        
        if token_success and api_success:
            print("🎉 All tests passed! Your eBay authentication is working correctly.")
            print("\nIf you're still getting errors in your app, check:")
            print("1. That your app is using the same environment variables")
            print("2. That your app is deployed with the latest code")
            print("3. Railway deployment logs for any startup errors")
            return
        
        if not token_success:
            print("❌ Token request failed. Here's how to fix it:")
            print("\n1. Verify your eBay App credentials:")
            print("   - Go to https://developer.ebay.com/")
            print("   - Login to your developer account")
            print("   - Go to 'My Account' → 'Application Keysets'")
            print("   - Find your app and copy the App ID and Cert ID")
            print("\n2. Check Railway environment variables:")
            print("   - Go to your Railway project dashboard")
            print("   - Click on your service")
            print("   - Go to 'Variables' tab")
            print("   - Ensure these are set:")
            print("     EBAY_CLIENT_ID = Your App ID")
            print("     EBAY_CLIENT_SECRET = Your Cert ID")
            print("\n3. Variable naming is critical:")
            print("   - Must be exactly: EBAY_CLIENT_ID (not EBAY_APP_ID)")
            print("   - Must be exactly: EBAY_CLIENT_SECRET (not EBAY_CERT_ID)")
            print("\n4. After setting variables, you must redeploy:")
            print("   - Click the 'Deploy' button in Railway")
            print("   - Or push a new commit to trigger deployment")
            
        elif not api_success:
            print("❌ Token works but API calls fail. Possible issues:")
            print("1. Your eBay app might not be approved for production")
            print("2. Your app might have insufficient permissions")
            print("3. You might be using sandbox credentials in production")
            print("4. Network connectivity issues")
    
    async def run_full_diagnosis(self):
        """Run the complete diagnostic process."""
        print("🚀 Starting eBay Authentication Diagnosis...")
        print("This will help identify and fix your authentication issues.")
        
        # Step 1: Check environment variables
        env_ok = self.check_environment_variables()
        
        if not env_ok:
            self.provide_troubleshooting_steps(False, False)
            return
        
        # Step 2: Test token request
        token = await self.test_token_request()
        token_success = token is not None
        
        # Step 3: Test API call if token works
        api_success = False
        if token_success:
            api_success = await self.test_api_call(token)
        
        # Step 4: Test app integration
        await self.check_app_client_integration()
        
        # Step 5: Provide troubleshooting
        self.provide_troubleshooting_steps(token_success, api_success)
        
        # Final summary
        self.print_section("Summary")
        print(f"Environment Variables: {'✅' if env_ok else '❌'}")
        print(f"Token Request: {'✅' if token_success else '❌'}")
        print(f"API Call: {'✅' if api_success else '❌'}")
        
        if env_ok and token_success and api_success:
            print("\n🎉 Your eBay authentication is working perfectly!")
            print("If you're still having issues, the problem might be:")
            print("1. Code deployment issues")
            print("2. Railway-specific configuration problems")
            print("3. Port configuration issues")
        else:
            print("\n🔧 Please follow the troubleshooting steps above.")

async def main():
    """Main function to run the diagnostic."""
    debugger = EbayAuthDebugger()
    await debugger.run_full_diagnosis()

if __name__ == "__main__":
    asyncio.run(main()) 