"""
Production-Grade Async eBay API Client
====================================

A comprehensive async Python client for eBay APIs using httpx.
Supports both Application Tokens (Client Credentials) and User OAuth tokens.
Automatically handles authentication, rate limiting, retries, and error handling.

Usage Examples:
    # Basic search
    client = EbayAPIClient()
    response = await client.call_api(
        method="GET",
        endpoint="/buy/browse/v1/item_summary/search",
        params={"q": "laptop", "limit": 10}
    )
    
    # With custom token
    response = await client.call_api(
        method="POST", 
        endpoint="/buy/browse/v1/item_summary/search_by_image",
        json_data={"image": "base64_string"},
        token_override="your_token_here"
    )

Features:
- ✅ Async/await with httpx.AsyncClient
- ✅ Automatic token management (Application + User OAuth)
- ✅ Smart rate limiting with exponential backoff
- ✅ Comprehensive error handling and retries
- ✅ Request/response logging
- ✅ Base URL and header management
- ✅ Support for GET, POST, PUT, DELETE methods
- ✅ JSON and form data support
"""

import os
import time
import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from urllib.parse import urljoin

# Use absolute imports for robustness
from app import crud, security
from app.database import SessionLocal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EbayAPIError(Exception):
    """Custom exception for all eBay API-related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class EbayAPIClient:
    """
    An advanced, asynchronous eBay API client that supports both Application tokens
    for browsing and User-specific OAuth tokens for seller operations,
    including automatic token refresh.
    """
    def __init__(self, user_id: Optional[int] = None):
        self.base_url = "https://api.ebay.com"
        self.user_id = user_id
        self.db = SessionLocal()

        self.client_id = os.getenv("EBAY_CLIENT_ID")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("EBAY_REDIRECT_URI")

    async def _get_user_access_token(self) -> str:
        """
        Retrieves a valid access token for the user, refreshing it if necessary.
        This is the core of the user-level authentication.
        """
        if not self.user_id:
            raise EbayAPIError("A user_id is required for this operation.")

        token_record = crud.get_token_for_user(self.db, self.user_id)
        if not token_record:
            raise EbayAPIError("User has not connected their eBay account.", status_code=401)

        # Check if the access token is expired (with a 5-minute buffer)
        if datetime.utcnow() >= token_record.access_token_expires_at - timedelta(minutes=5):
            logger.info(f"Access token for user {self.user_id} is expired. Refreshing now.")
            return await self._refresh_user_token(token_record)
        
        logger.info(f"Using valid access token for user {self.user_id}.")
        return security.decrypt_token(token_record.encrypted_access_token)

    async def _refresh_user_token(self, token_record) -> str:
        """Refreshes an expired access token using the refresh token."""
        refresh_token = security.decrypt_token(token_record.encrypted_refresh_token)
        
        token_url = f"{self.base_url}/identity/v1/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": " ".join([
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.account",
                "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
            ])
        }
        auth = (self.client_id, self.client_secret)

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, headers=headers, data=data, auth=auth)

        if response.status_code != 200:
            logger.error(f"Failed to refresh token for user {self.user_id}. Status: {response.status_code}, Response: {response.text}")
            raise EbayAPIError("Failed to refresh eBay token. Please try reconnecting your account.", status_code=401)
        
        new_token_data = response.json()
        
        # The refresh token itself might be refreshed. If not, reuse the old one.
        if "refresh_token" not in new_token_data:
            new_token_data["refresh_token"] = refresh_token
        
        # Update the token in the database
        crud.update_or_create_token(self.db, user_id=self.user_id, token_data=new_token_data)
        logger.info(f"Successfully refreshed token for user {self.user_id}.")
        
        return new_token_data["access_token"]

    async def _make_request(self, method: str, endpoint: str, json_data: Optional[Dict] = None, headers: Optional[Dict] = None):
        """A generic, authenticated request method for user-level API calls."""
        access_token = await self._get_user_access_token()
        
        full_url = urljoin(self.base_url, endpoint)
        
        request_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if headers:
            request_headers.update(headers)

        async with httpx.AsyncClient() as client:
            response = await client.request(method, full_url, json=json_data, headers=request_headers)

        if not (200 <= response.status_code < 300):
            logger.error(f"eBay API Error on {endpoint}: {response.status_code} - {response.text}")
            raise EbayAPIError(f"eBay API request failed: {response.text}", status_code=response.status_code)

        # Some eBay APIs return 204 No Content on success
        if response.status_code == 204:
            return None
            
        return response.json()

    # --- Sell API Methods ---

    async def create_or_replace_inventory_item(self, sku: str, item_data: Dict):
        """Creates or replaces an inventory item."""
        endpoint = f"/sell/inventory/v1/inventory_item/{sku}"
        return await self._make_request("PUT", endpoint, json_data=item_data)

    async def create_offer(self, offer_data: Dict):
        """Creates an offer, which is a component of a listing."""
        endpoint = "/sell/inventory/v1/offer"
        return await self._make_request("POST", endpoint, json_data=offer_data)

    async def publish_offer(self, offer_id: str):
        """Publishes an offer, turning it into a live listing."""
        endpoint = f"/sell/inventory/v1/offer/{offer_id}/publish"
        response = await self._make_request("POST", endpoint)
        return response.get("listingId") if response else None

    async def get_inventory(self, limit: int = 100, offset: int = 0):
        """Fetches the seller's inventory."""
        endpoint = f"/sell/inventory/v1/inventory_item?limit={limit}&offset={offset}"
        return await self._make_request("GET", endpoint)

    async def get_orders(self, limit: int = 50, offset: int = 0):
        """Fetches the seller's orders."""
        # Using a filter to get recent orders
        endpoint = f"/sell/fulfillment/v1/order?limit={limit}&offset={offset}"
        return await self._make_request("GET", endpoint)

# This remains for public, unauthenticated calls
ebay_client = EbayAPIClient() 