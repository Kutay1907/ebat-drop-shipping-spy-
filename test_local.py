#!/usr/bin/env python3
"""
Quick test script to verify the eBay API client is working directly.

This script will:
1. Load your eBay API credentials from the .env file.
2. Call the search_products method in your EbayAPIClient.
3. Print the results to the console.

Before running, make sure your .env file has:
EBAY_CLIENT_ID=Your-App-ID
EBAY_CLIENT_SECRET=Your-Cert-ID
"""

import asyncio
import os
import json

# A simple way to load .env files for local development
def load_dotenv(filepath=".env"):
    if not os.path.exists(filepath):
        return
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# It's important to load environment variables before importing the client
# as it reads them upon initialization.
load_dotenv()

from app.ebay_api_client import ebay_client, EbayAPIError

async def test_ebay_search():
    """Test the search_products method of the EbayAPIClient."""
    print("🧪 Testing EbayAPIClient.search_products...")
    print("-" * 50)

    if not os.getenv("EBAY_CLIENT_ID") or not os.getenv("EBAY_CLIENT_SECRET"):
        print("❌ ERROR: EBAY_CLIENT_ID and EBAY_CLIENT_SECRET must be set in your .env file.")
        return

    try:
        # Use the pre-configured global client instance
        search_keyword = "drone"
        print(f"🚀 Searching for: '{search_keyword}'")
        
        results = await ebay_client.search_products(keyword=search_keyword, limit=5)
        
        print("✅ Search API call successful!")
        
        # Print a summary of the results
        metadata = results.get("search_metadata", {})
        print(f"   - Marketplace: {metadata.get('marketplace')}")
        print(f"   - Total results found: {metadata.get('total_results')}")
        
        item_summaries = results.get("itemSummaries", [])
        print(f"   - Displaying {len(item_summaries)} results:")

        if not item_summaries:
            print("   - No items found for this search.")
        else:
            for i, item in enumerate(item_summaries):
                title = item.get("title", "No Title")
                price = item.get("price", {}).get("value", "N/A")
                currency = item.get("price", {}).get("currency", "")
                item_id = item.get("itemId", "N/A")
                print(f"     {i+1}. {title[:60]}...")
                print(f"        Price: {price} {currency}")
                print(f"        ItemID: {item_id}")

    except EbayAPIError as e:
        print(f"❌ eBay API Error: {e.message}")
        print(f"   - Status Code: {e.status_code}")
        print(f"   - Response: {json.dumps(e.response_data, indent=2)}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

    print("-" * 50)
    print("🎉 Testing complete!")

if __name__ == "__main__":
    # To run this async script
    asyncio.run(test_ebay_search()) 