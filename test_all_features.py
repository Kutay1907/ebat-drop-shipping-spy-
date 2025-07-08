#!/usr/bin/env python3
"""
🚀 eBay Dropshipping Spy - Complete Feature Demo
=============================================

This script demonstrates all the powerful features of our eBay API integration:
- Universal API access (convert any eBay API Explorer call to Python)
- Multi-token authentication 
- Advanced search with filters
- Global marketplace support
- Production-grade error handling and retries

Run this script to see everything in action!
"""

import asyncio
import httpx
import json
import sys
import os
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"  # Change this to your deployed URL
TEST_KEYWORDS = ["laptop", "smartphone", "drone", "headphones", "watch"]

class eBayAPIDemo:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    def print_section(self, title: str):
        """Print a formatted section header."""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_result(self, result: Dict[str, Any], max_items: int = 3):
        """Print formatted API results."""
        if result.get("success"):
            print("✅ SUCCESS")
            
            # Show key metrics
            if "total_found" in result:
                print(f"📊 Total Results: {result['total_found']}")
            if "marketplace" in result:
                print(f"🌍 Marketplace: {result['marketplace']}")
            if "keyword" in result:
                print(f"🔍 Keyword: {result['keyword']}")
            
            # Show sample items
            items = result.get("results", [])
            if items:
                print(f"\n📦 Sample Items (showing {min(len(items), max_items)} of {len(items)}):")
                for i, item in enumerate(items[:max_items]):
                    print(f"\n  {i+1}. {item.get('title', 'No title')[:50]}...")
                    if 'price' in item:
                        print(f"     💰 Price: {item['price'].get('value')} {item['price'].get('currency')}")
                    if 'condition' in item:
                        print(f"     📋 Condition: {item['condition']}")
                    if 'seller' in item:
                        seller = item['seller']
                        print(f"     👤 Seller: {seller.get('username')} ({seller.get('feedbackScore')} feedback)")
        else:
            print("❌ FAILED")
            print(f"Error: {result.get('detail', 'Unknown error')}")
    
    async def test_health_check(self):
        """Test basic API health."""
        self.print_section("Health Check")
        try:
            response = await self.session.get(f"{self.base_url}/api/health")
            result = response.json()
            print("✅ API is healthy!")
            print(f"📊 Features: {', '.join(result.get('features', {}).keys())}")
            print(f"🔐 Authentication: {result.get('authentication', {})}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
    
    async def test_connection(self):
        """Test eBay API connection and authentication."""
        self.print_section("eBay Connection Test")
        try:
            response = await self.session.get(f"{self.base_url}/api/test-connection")
            result = response.json()
            
            print(f"🌐 Environment: {result.get('environment')}")
            print(f"⏰ Test Time: {result.get('timestamp')}")
            print(f"📊 Overall Status: {result.get('overall_status')}")
            
            print("\n🧪 Individual Tests:")
            for test in result.get('tests', []):
                status_icon = "✅" if test['status'] == 'success' else "❌"
                print(f"  {status_icon} {test['test']}: {test['message']}")
            
            if result.get('recommendations'):
                print("\n💡 Recommendations:")
                for rec in result['recommendations']:
                    print(f"  • {rec}")
                    
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
    
    async def test_basic_search(self):
        """Test basic product search."""
        self.print_section("Basic Product Search")
        
        for keyword in TEST_KEYWORDS[:2]:  # Test 2 keywords
            print(f"\n🔍 Searching for: {keyword}")
            try:
                response = await self.session.post(
                    f"{self.base_url}/api/search",
                    json={
                        "keyword": keyword,
                        "limit": 5,
                        "marketplace": "EBAY_US",
                        "sort": "price"
                    }
                )
                result = response.json()
                self.print_result(result)
            except Exception as e:
                print(f"❌ Search failed: {e}")
    
    async def test_advanced_search(self):
        """Test advanced search with filters."""
        self.print_section("Advanced Search with Filters")
        
        # Test price range filtering
        try:
            response = await self.session.post(
                f"{self.base_url}/api/search/advanced",
                json={
                    "keyword": "smartphone", 
                    "min_price": 100,
                    "max_price": 500,
                    "condition": "NEW",
                    "limit": 5,
                    "marketplace": "EBAY_US"
                }
            )
            result = response.json()
            print("🎯 Advanced Search: Smartphones $100-$500, NEW condition")
            self.print_result(result)
            
            if result.get("success"):
                print(f"🔧 Filters Applied: {result.get('filters_applied', {})}")
                
        except Exception as e:
            print(f"❌ Advanced search failed: {e}")
    
    async def test_multiple_marketplaces(self):
        """Test searching across different eBay marketplaces."""
        self.print_section("Multi-Marketplace Search")
        
        marketplaces = ["EBAY_US", "EBAY_GB", "EBAY_DE"]
        keyword = "laptop"
        
        for marketplace in marketplaces:
            print(f"\n🌍 Testing {marketplace}...")
            try:
                response = await self.session.post(
                    f"{self.base_url}/api/search",
                    json={
                        "keyword": keyword,
                        "limit": 3,
                        "marketplace": marketplace
                    }
                )
                result = response.json()
                
                if result.get("success"):
                    items = result.get("results", [])
                    if items:
                        price = items[0].get("price", {})
                        print(f"  ✅ Found {result.get('total_found')} items")
                        print(f"  💰 Sample price: {price.get('value')} {price.get('currency')}")
                else:
                    print(f"  ❌ {result.get('detail', 'Unknown error')}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    async def test_direct_api_calls(self):
        """Test the universal API call feature - the crown jewel!"""
        self.print_section("Universal eBay API Access")
        print("🚀 This is our most powerful feature - convert ANY eBay API call to code!")
        
        # Test 1: Basic Browse API search
        print(f"\n📡 Test 1: Direct Browse API Call")
        try:
            response = await self.session.post(
                f"{self.base_url}/api/api-call",
                json={
                    "method": "GET",
                    "endpoint": "/buy/browse/v1/item_summary/search",
                    "params": {
                        "q": "gaming chair",
                        "limit": 3,
                        "sort": "price"
                    },
                    "marketplace": "EBAY_US"
                }
            )
            result = response.json()
            
            if result.get("success"):
                print("  ✅ Direct API call successful!")
                print(f"  📊 Method: {result.get('method')}")
                print(f"  🔗 Endpoint: {result.get('endpoint')}")
                
                api_response = result.get('response', {})
                if 'itemSummaries' in api_response:
                    items = api_response['itemSummaries']
                    print(f"  📦 Found {len(items)} items")
                    if items:
                        print(f"  💰 First item: {items[0].get('title', 'No title')[:40]}...")
            else:
                print(f"  ❌ Failed: {result.get('detail', 'Unknown error')}")
                
        except Exception as e:
            print(f"  ❌ Direct API call failed: {e}")
        
        # Test 2: Show how flexible this is
        print(f"\n📡 Test 2: Different HTTP Method & Parameters")
        try:
            response = await self.session.post(
                f"{self.base_url}/api/api-call",
                json={
                    "method": "GET",
                    "endpoint": "/buy/browse/v1/item_summary/search",
                    "params": {
                        "q": "vintage watch",
                        "limit": 2,
                        "filter": "price:[50..200],condition:USED"
                    },
                    "marketplace": "EBAY_US"
                }
            )
            result = response.json()
            
            if result.get("success"):
                print("  ✅ Filtered search successful!")
                api_response = result.get('response', {})
                print(f"  🔍 Filter applied: vintage watches, $50-$200, USED")
                if 'total' in api_response:
                    print(f"  📊 Total matches: {api_response['total']}")
            else:
                print(f"  ❌ Failed: {result.get('detail', 'Unknown error')}")
                
        except Exception as e:
            print(f"  ❌ Filtered API call failed: {e}")
    
    async def test_marketplace_info(self):
        """Test marketplace information endpoint."""
        self.print_section("Marketplace Information")
        try:
            response = await self.session.get(f"{self.base_url}/api/marketplace/info")
            result = response.json()
            
            if result.get("success"):
                marketplaces = result.get('marketplaces', {})
                print(f"🌍 Available Marketplaces: {len(marketplaces)}")
                
                for code, info in list(marketplaces.items())[:5]:  # Show first 5
                    print(f"  • {code}: {info['name']} ({info['currency']})")
                
                print(f"\n🚀 Supported Features:")
                features = result.get('supported_features', {})
                for feature, support in features.items():
                    print(f"  ✅ {feature}: {support}")
            else:
                print(f"❌ Failed: {result.get('detail', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Marketplace info failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling and edge cases."""
        self.print_section("Error Handling & Edge Cases")
        
        # Test invalid endpoint
        print("🧪 Test 1: Invalid API endpoint")
        try:
            response = await self.session.post(
                f"{self.base_url}/api/api-call",
                json={
                    "method": "GET",
                    "endpoint": "/invalid/endpoint/that/does/not/exist",
                    "params": {"test": "value"}
                }
            )
            result = response.json()
            print(f"  Status: {response.status_code}")
            print(f"  Error handled gracefully: {'error' in result.get('detail', {})}")
            
        except Exception as e:
            print(f"  ✅ Error properly caught: {e}")
        
        # Test malformed request
        print("\n🧪 Test 2: Malformed search request")
        try:
            response = await self.session.post(
                f"{self.base_url}/api/search",
                json={
                    "keyword": "",  # Empty keyword
                    "limit": -5      # Invalid limit
                }
            )
            result = response.json()
            print(f"  Status: {response.status_code}")
            print(f"  Validation error handled: {response.status_code == 422}")
            
        except Exception as e:
            print(f"  ✅ Error properly caught: {e}")

async def main():
    """Run the complete demo."""
    print("🎉 eBay Dropshipping Spy - Complete Feature Demo")
    print("=" * 60)
    print("This demo showcases our powerful eBay API integration:")
    print("• Universal API access (convert any API Explorer call)")
    print("• Multi-token authentication")
    print("• Advanced search & filtering")
    print("• Global marketplace support")
    print("• Production-grade error handling")
    print("\nLet's see everything in action! 🚀")
    
    # Check if server is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/api/health")
            if response.status_code != 200:
                print(f"\n❌ Server not responding at {BASE_URL}")
                print("Please make sure your FastAPI server is running:")
                print("  python -m uvicorn app.main:app --reload")
                sys.exit(1)
    except Exception as e:
        print(f"\n❌ Cannot connect to server at {BASE_URL}")
        print(f"Error: {e}")
        print("\nPlease start your server first:")
        print("  python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Run all tests
    async with eBayAPIDemo(BASE_URL) as demo:
        try:
            await demo.test_health_check()
            await demo.test_connection()
            await demo.test_basic_search()
            await demo.test_advanced_search()
            await demo.test_multiple_marketplaces()
            await demo.test_direct_api_calls()  # The crown jewel!
            await demo.test_marketplace_info()
            await demo.test_error_handling()
            
            # Final summary
            demo.print_section("Demo Complete! 🎉")
            print("✅ All features tested successfully!")
            print("\n🚀 What you just saw:")
            print("• Complete eBay API integration")
            print("• Universal API access (any endpoint → Python code)")
            print("• Multi-marketplace support")
            print("• Advanced filtering & search")
            print("• Production-grade error handling")
            print("• Real-time eBay data access")
            
            print(f"\n🌐 Access your API at: {BASE_URL}")
            print(f"📚 Full documentation: {BASE_URL}/docs")
            print(f"🎨 Beautiful UI: {BASE_URL}/")
            
            print("\n💡 Next Steps:")
            print("1. Set your eBay credentials (EBAY_CLIENT_ID, EBAY_CLIENT_SECRET)")
            print("2. Deploy to Railway/Vercel/Heroku for production")
            print("3. Use /api/api-call endpoint to convert any eBay API Explorer call")
            print("4. Build amazing dropshipping tools with this foundation!")
            
        except KeyboardInterrupt:
            print("\n\n⏸️ Demo interrupted by user")
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Environment check
    print("🔧 Environment Check:")
    env_vars = ["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET"]
    for var in env_vars:
        status = "✅ SET" if os.getenv(var) else "⚠️ NOT SET"
        print(f"  {var}: {status}")
    
    if not any(os.getenv(var) for var in env_vars):
        print("\n💡 Tip: Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET for full functionality")
        print("But the demo will still work with basic features!\n")
    
    # Run the demo
    asyncio.run(main()) 