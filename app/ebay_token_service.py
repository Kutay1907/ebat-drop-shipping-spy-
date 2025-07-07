"""
eBay Application Token Service - Client Credentials Grant Flow
For eBay Browse API (product search) - no user consent required
"""

import os
import time
import requests
import asyncio
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EbayApplicationTokenService:
    def __init__(self):
        self.client_id = os.getenv("EBAY_CLIENT_ID")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET")
        self.token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        self._token_cache = None
        self._token_expires_at = 0
        
    def _is_token_valid(self) -> bool:
        """Check if cached token is still valid (with 5 minute buffer)"""
        if not self._token_cache:
            return False
        return time.time() < (self._token_expires_at - 300)  # 5 min buffer
    
    async def get_application_token(self) -> Optional[str]:
        """
        Get a valid Application token for eBay Browse API.
        Uses Client Credentials grant flow - no user consent needed.
        """
        if self._is_token_valid():
            logger.info("Using cached eBay application token")
            return self._token_cache
            
        if not self.client_id or not self.client_secret:
            logger.error("eBay credentials not configured")
            return None
            
        try:
            # Use asyncio.to_thread to run sync request in async context
            token_data = await asyncio.to_thread(self._request_new_token)
            if token_data:
                self._token_cache = token_data["access_token"]
                # eBay tokens expire in 2 hours (7200 seconds)
                self._token_expires_at = time.time() + token_data.get("expires_in", 7200)
                logger.info("Successfully obtained new eBay application token")
                return self._token_cache
        except Exception as e:
            logger.error(f"Failed to get eBay application token: {e}")
            
        return None
    
    def _request_new_token(self) -> Optional[Dict[str, Any]]:
        """Request new application token from eBay (sync method)"""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self._get_basic_auth()}"
        }
        
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
        
        response = requests.post(
            self.token_url,
            headers=headers,
            data=data,
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"eBay token request failed: {response.status_code} - {response.text}")
            return None
    
    def _get_basic_auth(self) -> str:
        """Generate Basic Auth header value"""
        import base64
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()

# Global instance
ebay_token_service = EbayApplicationTokenService() 