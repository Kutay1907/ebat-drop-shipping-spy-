"""
Production-Grade Async eBay API Client
====================================

A comprehensive async Python client for eBay APIs using httpx.
It supports two authentication modes:
1. Application Tokens (Client Credentials Grant): For public-facing API calls
   like search, which do not require user-specific permissions.
2. User OAuth Tokens (Authorization Code Grant): For making API calls on
   behalf of a user who has connected their eBay account.

Features:
- ✅ Dual-mode authentication (Application & User)
- ✅ Automatic, cached token management for both modes
- ✅ Smart rate limiting with exponential backoff (to be implemented)
- ✅ Comprehensive error handling and retries (to be implemented)
- ✅ Request/response logging
- ✅ Centralized httpx client session
"""

import os
import time
import httpx
import logging
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin
import asyncio
from functools import wraps
from sqlalchemy.orm import Session

from app import crud, security, models
from app.database import SessionLocal, get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- In-memory cache for Application Token ---
app_token_cache: Dict[str, Any] = {
    "token": None,
    "expires_at": None
}
app_token_lock = asyncio.Lock()


class EbayAPIError(Exception):
    """Custom exception for all eBay API-related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(f"Status {status_code}: {message}")

class EbayAPIClient:
    """
    An advanced, asynchronous eBay API client that supports both Application tokens
    for browsing and User-specific OAuth tokens for seller operations.
    """
    def __init__(self, user_id: Optional[int] = None):
        self.base_url = "https://api.ebay.com"
        self.user_id = user_id
        
        self.client_id = os.getenv("EBAY_CLIENT_ID")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise ValueError("EBAY_CLIENT_ID and EBAY_CLIENT_SECRET must be set.")

    async def _get_auth_header(self) -> Dict[str, str]:
        """
        Determines which token to use (Application or User) and returns the
        appropriate Authorization header.
        """
        if self.user_id:
            db = next(get_db())
            try:
                token = await self._get_user_access_token(db)
            finally:
                db.close()
                
            if not token:
                raise EbayAPIError("User is not authenticated or token is invalid.", status_code=401)
            return {"Authorization": f"Bearer {token}"}
        else:
            token = await self._get_application_access_token()
            if not token:
                raise EbayAPIError("Could not retrieve application token for public API access.", status_code=500)
            return {"Authorization": f"Bearer {token}"}

    async def _get_application_access_token(self) -> str:
        """
        Retrieves a valid Application access token using the Client Credentials Grant flow.
        The token is cached in memory to improve performance.
        """
        async with app_token_lock:
            if app_token_cache["token"] and isinstance(app_token_cache["expires_at"], datetime) and app_token_cache["expires_at"] > datetime.utcnow() + timedelta(minutes=5):
                logger.info("Using cached eBay application token.")
                return str(app_token_cache["token"])

            logger.info("Application token expired or not found. Fetching new one.")
            token_url = f"{self.base_url}/identity/v1/oauth2/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope"
            }
            # Ensure credentials are not None before using them
            assert self.client_id is not None
            assert self.client_secret is not None
            auth = (self.client_id, self.client_secret)
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(token_url, headers=headers, data=data, auth=auth)
                response.raise_for_status()
                
                token_data = response.json()
                access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 7200)

                app_token_cache["token"] = access_token
                app_token_cache["expires_at"] = datetime.utcnow() + timedelta(seconds=expires_in)
                
                logger.info("Successfully fetched and cached new application token.")
                return access_token
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to get application token: {e.response.status_code} - {e.response.text}")
                raise EbayAPIError(f"eBay authentication failed: {e.response.text}", status_code=e.response.status_code)
            except Exception as e:
                logger.error(f"An unexpected error occurred while getting application token: {e}")
                raise EbayAPIError(f"An unexpected error occurred: {e}")

    async def _get_user_access_token(self, db: Session) -> Optional[str]:
        """
        Retrieves a valid access token for the user from the database,
        refreshing it if necessary.
        """
        if not self.user_id:
            return None

        token_record = crud.get_token_for_user(db, self.user_id)
        if not token_record:
            return None

        # Explicitly cast the comparison to bool
        is_expired = bool(datetime.utcnow() >= token_record.access_token_expires_at - timedelta(minutes=5))
        if is_expired:
            logger.info(f"Access token for user {self.user_id} is expired. Refreshing now.")
            return await self._refresh_user_token(token_record, db)
        
        logger.info(f"Using valid access token for user {self.user_id}.")
        return security.decrypt_token(str(token_record.encrypted_access_token))

    async def _refresh_user_token(self, token_record: models.EbayOAuthToken, db: Session) -> str:
        """Refreshes an expired user access token."""
        decrypted_refresh_token = security.decrypt_token(str(token_record.encrypted_refresh_token))
        
        token_url = f"{self.base_url}/identity/v1/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "refresh_token",
            "refresh_token": decrypted_refresh_token,
            "scope": "https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment"
        }
        # Ensure credentials are not None before using them
        assert self.client_id is not None
        assert self.client_secret is not None
        auth = (self.client_id, self.client_secret)

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, headers=headers, data=data, auth=auth)

        if response.status_code != 200:
            logger.error(f"Failed to refresh token for user {self.user_id}. Status: {response.status_code}, Response: {response.text}")
            raise EbayAPIError("Failed to refresh eBay token. Please try reconnecting your account.", status_code=401)
        
        new_token_data = response.json()
        
        if "refresh_token" not in new_token_data:
            new_token_data["refresh_token"] = decrypted_refresh_token
        
        if self.user_id:
            crud.update_or_create_token(db, user_id=self.user_id, token_data=new_token_data)
            logger.info(f"Successfully refreshed and updated token for user {self.user_id}.")
        
        return str(new_token_data["access_token"])

    async def call_api(self, method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None, headers: Optional[Dict] = None):
        """
        A generic, authenticated request method for all eBay API calls.
        It automatically handles getting the correct token (Application or User).
        """
        auth_header = await self._get_auth_header()
        
        full_url = urljoin(self.base_url, endpoint)
        
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        request_headers.update(auth_header)
        if headers:
            request_headers.update(headers)
        
        logger.info(f"Making API call: {method} {full_url}")
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.request(method, full_url, params=params, json=json_data, headers=request_headers)
                response.raise_for_status()
                
                if response.status_code == 204:
                    return None
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(f"eBay API Error on {endpoint}: {e.response.status_code} - {e.response.text}")
                raise EbayAPIError(f"eBay API request failed: {e.response.text}", status_code=e.response.status_code)
            except httpx.RequestError as e:
                logger.error(f"Network error calling eBay API on {endpoint}: {e}")
                raise EbayAPIError(f"A network error occurred: {e}", status_code=503)

# Global Client Instance for Public Calls
ebay_client = EbayAPIClient()

# Helper function for user-specific calls
def get_user_ebay_client(user_id: int) -> EbayAPIClient:
    return EbayAPIClient(user_id=user_id) 