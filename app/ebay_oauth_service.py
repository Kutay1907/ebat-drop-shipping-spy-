"""
eBay OAuth 2.0 Service - Production Ready Implementation
=====================================================

This service implements eBay's OAuth 2.0 authorization code flow according to 
eBay Developer Program specifications. It handles user authentication, token 
management, and automatic refresh functionality.

Key Features:
- eBay-specific OAuth 2.0 implementation
- RuName-based redirect handling
- Automatic token refresh
- Secure token storage with encryption
- Multi-user support
"""

import os
import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode
from sqlalchemy.orm import Session

from . import crud, security, models

logger = logging.getLogger(__name__)

class EbayOAuthService:
    """
    Complete eBay OAuth 2.0 service following eBay Developer Program specifications.
    
    This service handles the full OAuth flow for eBay user authentication including:
    - Authorization code generation
    - Token exchange and refresh
    - Secure token storage
    - User session management
    """
    
    def __init__(self):
        self.client_id = os.getenv("EBAY_CLIENT_ID")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET")
        # Clean the RuName by removing any whitespace or newlines
        raw_redirect_uri = os.getenv("EBAY_REDIRECT_URI", "")
        self.redirect_uri = raw_redirect_uri.strip() if raw_redirect_uri else None
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        
        # eBay OAuth 2.0 endpoints (Production)
        self.auth_url = "https://auth.ebay.com/oauth2/authorize"
        self.token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        
        # eBay OAuth 2.0 scopes for selling applications
        self.scopes = [
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly", 
            "https://api.ebay.com/oauth/api_scope/sell.account",
            "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
            "https://api.ebay.com/oauth/api_scope/sell.marketing",
            "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly",
            "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
            "https://api.ebay.com/oauth/api_scope/sell.finances"
        ]
        
        self._validate_credentials()
        
        # Log the cleaned RuName for verification
        logger.info(f"Initialized eBay OAuth service with RuName: {self.redirect_uri}")
    
    def _validate_credentials(self):
        """Validate that all required credentials are present and properly formatted."""
        missing_creds = []
        
        if not self.client_id:
            missing_creds.append("EBAY_CLIENT_ID")
        if not self.client_secret:
            missing_creds.append("EBAY_CLIENT_SECRET") 
        if not self.redirect_uri:
            missing_creds.append("EBAY_REDIRECT_URI")
        if not self.encryption_key:
            missing_creds.append("ENCRYPTION_KEY")
            
        if missing_creds:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_creds)}")
            
        # Validate RuName format
        if self.redirect_uri and ('\n' in self.redirect_uri or '\r' in self.redirect_uri):
            raise ValueError("EBAY_REDIRECT_URI contains invalid newline characters")
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate the eBay OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Complete eBay OAuth authorization URL
        """
        # eBay OAuth 2.0 authorization parameters
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,  # This should be your RuName
            "scope": " ".join(self.scopes)
        }
        
        if state:
            params["state"] = state
            
        url = f"{self.auth_url}?{urlencode(params)}"
        
        logger.info(f"Generated eBay OAuth URL with {len(self.scopes)} scopes")
        logger.info(f"Redirect URI (RuName): {self.redirect_uri}")
        
        return url
    
    async def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            authorization_code: The code returned from eBay's authorization flow
            
        Returns:
            Dictionary containing token information
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self._get_basic_auth()}"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(self.token_url, headers=headers, data=data)
            
            if response.status_code != 200:
                logger.error(f"eBay token exchange failed: {response.status_code} - {response.text}")
                raise Exception(f"Failed to exchange authorization code: {response.text}")
            
            token_data = response.json()
            logger.info("Successfully obtained eBay access and refresh tokens")
            
            return token_data
            
        except httpx.RequestError as e:
            logger.error(f"Request error during token exchange: {str(e)}")
            raise Exception(f"Network error during token exchange: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {str(e)}")
            raise
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token using the refresh token.
        
        Args:
            refresh_token: The refresh token (decrypted)
            
        Returns:
            New token data dictionary
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {self._get_basic_auth()}"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": " ".join(self.scopes)
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(self.token_url, headers=headers, data=data)
            
            if response.status_code != 200:
                logger.error(f"eBay token refresh failed: {response.status_code} - {response.text}")
                raise Exception(f"Failed to refresh access token: {response.text}")
            
            token_data = response.json()
            
            # eBay may not always return a new refresh token
            if "refresh_token" not in token_data:
                token_data["refresh_token"] = refresh_token
                
            logger.info("Successfully refreshed eBay access token")
            return token_data
            
        except httpx.RequestError as e:
            logger.error(f"Request error during token refresh: {str(e)}")
            raise Exception(f"Network error during token refresh: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            raise
    
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
            logger.info(f"Stored encrypted eBay tokens for user {user_id}")
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
            # Get the actual string value from the Column
            encrypted_token = str(token_record.encrypted_access_token)
            return security.decrypt_token(encrypted_token)
        except Exception as e:
            logger.error(f"Failed to decrypt access token for user {user_id}: {str(e)}")
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
        # Convert SQLAlchemy DateTime to Python datetime
        expires_at = token_record.access_token_expires_at
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
        # Explicitly convert the comparison result to bool
        return bool(datetime.utcnow() >= expires_at - buffer_time)
    
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
            logger.warning(f"No eBay token found for user {user_id}")
            return None
        
        # Check if token needs refresh
        if self.is_token_expired(db, user_id):
            logger.info(f"eBay token expired for user {user_id}, refreshing...")
            
            try:
                # Get and decrypt refresh token
                encrypted_token = str(token_record.encrypted_refresh_token)
                refresh_token = security.decrypt_token(encrypted_token)
                
                # Refresh the token
                new_token_data = await self.refresh_access_token(refresh_token)
                
                # Store the new tokens
                self.store_user_tokens(db, user_id, new_token_data)
                
                # Return the new access token
                return new_token_data["access_token"]
                
            except Exception as e:
                logger.error(f"Failed to refresh eBay token for user {user_id}: {str(e)}")
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
            # Delete the user's token record
            token_record = self.get_stored_token(db, user_id)
            if token_record:
                db.delete(token_record)
                db.commit()
                logger.info(f"Disconnected eBay account for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to disconnect user {user_id}: {str(e)}")
            raise
    
    def _get_basic_auth(self) -> str:
        """Generate Basic Auth header value for eBay API requests."""
        import base64
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()

# Global instance
ebay_oauth = EbayOAuthService() 