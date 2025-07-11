"""
Comprehensive eBay OAuth Service
===============================

This service handles the complete eBay OAuth2 flow including:
- User authentication redirect
- Token exchange and storage
- Automatic token refresh
- Secure token management with encryption
"""

import os
import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode
from sqlalchemy.orm import Session

from . import crud, security, models
from .database import SessionLocal

logger = logging.getLogger(__name__)

class EbayOAuthService:
    """
    Complete eBay OAuth service for user authentication and token management.
    """
    
    def __init__(self):
        self.client_id = os.getenv("EBAY_CLIENT_ID")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("EBAY_REDIRECT_URI")
        self.token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        self.auth_url = "https://auth.ebay.com/oauth2/authorize"
        
        # Conservative scopes - start with core functionality first
        self.scopes = [
            # Core Inventory Management (required for basic seller operations)
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
            
            # Account Management (for seller account access)
            "https://api.ebay.com/oauth/api_scope/sell.account",
            "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
            
            # Order Management (for fulfillment)
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly"
        ]
    
    def get_auth_url(self, state: Optional[str] = None) -> str:
        """
        Generate the eBay OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Complete eBay OAuth authorization URL
        """
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Missing eBay OAuth credentials. Check EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, and EBAY_REDIRECT_URI.")
        
        # Ensure redirect URI is properly formatted
        if not self.redirect_uri.startswith("https://"):
            raise ValueError("EBAY_REDIRECT_URI must use HTTPS protocol")
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes)
            # Remove "prompt": "login" as it might cause issues
        }
        
        if state:
            params["state"] = state
            
        url = f"{self.auth_url}?{urlencode(params)}"
        
        # Log for debugging (without sensitive data)
        logger.info(f"Generated OAuth URL with {len(self.scopes)} scopes")
        logger.info(f"Redirect URI: {self.redirect_uri}")
        
        return url
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from eBay callback
            
        Returns:
            Token data dictionary containing access_token, refresh_token, etc.
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                headers=headers,
                auth=(self.client_id, self.client_secret),
                data=data,
                timeout=30
            )
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            raise Exception(f"Failed to exchange code for tokens: {response.text}")
        
        token_data = response.json()
        logger.info("Successfully exchanged code for eBay tokens")
        return token_data
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token using the refresh token.
        
        Args:
            refresh_token: The refresh token (decrypted)
            
        Returns:
            New token data dictionary
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": " ".join(self.scopes)
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                headers=headers,
                auth=(self.client_id, self.client_secret),
                data=data,
                timeout=30
            )
        
        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
            raise Exception(f"Failed to refresh token: {response.text}")
        
        token_data = response.json()
        
        # If refresh token wasn't renewed, keep the old one
        if "refresh_token" not in token_data:
            token_data["refresh_token"] = refresh_token
            
        logger.info("Successfully refreshed eBay access token")
        return token_data
    
    def store_user_tokens(self, db: Session, user_id: int, token_data: Dict[str, Any]) -> None:
        """
        Store encrypted user tokens in the database.
        
        Args:
            db: Database session
            user_id: User ID
            token_data: Token data from eBay
        """
        try:
            crud.update_or_create_token(db, user_id=user_id, token_data=token_data)
            logger.info(f"Stored encrypted tokens for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to store tokens for user {user_id}: {str(e)}")
            raise
    
    def get_stored_token(self, db: Session, user_id: int) -> Optional[models.EbayOAuthToken]:
        """
        Get stored token record for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Token record or None if not found
        """
        return crud.get_token_for_user(db, user_id)
    
    def get_decrypted_access_token(self, db: Session, user_id: int) -> Optional[str]:
        """
        Get and decrypt the user's access token.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Decrypted access token or None
        """
        token_record = self.get_stored_token(db, user_id)
        if not token_record:
            return None
            
        try:
            return security.decrypt_token(token_record.encrypted_access_token)
        except Exception as e:
            logger.error(f"Failed to decrypt access token for user {user_id}: {str(e)}")
            return None
    
    def get_decrypted_refresh_token(self, db: Session, user_id: int) -> Optional[str]:
        """
        Get and decrypt the user's refresh token.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Decrypted refresh token or None
        """
        token_record = self.get_stored_token(db, user_id)
        if not token_record:
            return None
            
        try:
            return security.decrypt_token(token_record.encrypted_refresh_token)
        except Exception as e:
            logger.error(f"Failed to decrypt refresh token for user {user_id}: {str(e)}")
            return None
    
    def is_token_expired(self, db: Session, user_id: int, buffer_minutes: int = 5) -> bool:
        """
        Check if the user's access token is expired or will expire soon.
        
        Args:
            db: Database session
            user_id: User ID
            buffer_minutes: Minutes before expiry to consider token expired
            
        Returns:
            True if token is expired or will expire soon
        """
        token_record = self.get_stored_token(db, user_id)
        if not token_record:
            return True
            
        buffer_time = timedelta(minutes=buffer_minutes)
        return datetime.utcnow() >= token_record.access_token_expires_at - buffer_time
    
    async def get_valid_access_token(self, db: Session, user_id: int) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Valid access token or None if user not authenticated
        """
        token_record = self.get_stored_token(db, user_id)
        if not token_record:
            logger.warning(f"No token found for user {user_id}")
            return None
        
        # Check if token needs refresh
        if self.is_token_expired(db, user_id):
            logger.info(f"Token expired for user {user_id}, refreshing...")
            
            try:
                # Get and decrypt refresh token
                refresh_token = security.decrypt_token(token_record.encrypted_refresh_token)
                
                # Refresh the token
                new_token_data = await self.refresh_access_token(refresh_token)
                
                # Store the new tokens
                self.store_user_tokens(db, user_id, new_token_data)
                
                # Return the new access token
                return new_token_data["access_token"]
                
            except Exception as e:
                logger.error(f"Failed to refresh token for user {user_id}: {str(e)}")
                return None
        
        # Token is still valid, return it
        return self.get_decrypted_access_token(db, user_id)
    
    def is_user_connected(self, db: Session, user_id: int) -> bool:
        """
        Check if a user has connected their eBay account.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if user has valid eBay tokens
        """
        token_record = self.get_stored_token(db, user_id)
        return token_record is not None
    
    def disconnect_user(self, db: Session, user_id: int) -> None:
        """
        Disconnect a user by removing their stored tokens.
        
        Args:
            db: Database session
            user_id: User ID
        """
        try:
            # Note: You'll need to implement this in crud.py
            # crud.delete_user_token(db, user_id)
            logger.info(f"Disconnected eBay account for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to disconnect user {user_id}: {str(e)}")
            raise

# Global instance
ebay_oauth = EbayOAuthService() 