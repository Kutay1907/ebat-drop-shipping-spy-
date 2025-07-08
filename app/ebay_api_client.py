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

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Union, List
from enum import Enum
import os
import json
from urllib.parse import urljoin

try:
    import httpx
except ImportError:
    raise ImportError("httpx is required. Install with: pip install httpx")

logger = logging.getLogger(__name__)

class EbayAPIError(Exception):
    """Custom exception for eBay API errors with detailed context."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None, endpoint: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        self.endpoint = endpoint
        super().__init__(self.message)

class EbayEnvironment(Enum):
    """eBay API environments."""
    PRODUCTION = "https://api.ebay.com"
    SANDBOX = "https://api.sandbox.ebay.com"

class TokenType(Enum):
    """Types of eBay authentication tokens."""
    APPLICATION = "application"
    USER_OAUTH = "user_oauth"
    MANUAL = "manual"

class EbayAPIClient:
    """
    Production-grade async eBay API client with comprehensive features.
    
    This client automatically handles:
    - Token management and refresh
    - Rate limiting and retries
    - Error handling and logging
    - Base URL and header management
    """
    
    def __init__(
        self,
        environment: EbayEnvironment = EbayEnvironment.PRODUCTION,
        default_timeout: float = 30.0,
        max_retries: int = 3,
        rate_limit_delay: float = 1.0
    ):
        """
        Initialize the eBay API client.
        
        Args:
            environment: Production or Sandbox environment
            default_timeout: Default request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            rate_limit_delay: Base delay between retries (seconds)
        """
        self.base_url = environment.value
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        
        # Token management
        self._application_token_cache: Optional[str] = None
        self._application_token_expires_at: float = 0.0
        
        # Rate limiting
        self._last_request_time: float = 0.0
        self._min_request_interval: float = 0.1  # 10 requests per second max
        
        # Client credentials from environment
        self.client_id = os.getenv("EBAY_CLIENT_ID")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET")
        
        logger.info(f"Initialized eBay API Client for {environment.value}")

    async def call_api(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        token_override: Optional[str] = None,
        timeout: Optional[float] = None,
        marketplace_id: str = "EBAY_US",
        retry_on_auth_failure: bool = True
    ) -> Dict[str, Any]:
        """
        Make an authenticated API call to any eBay endpoint.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path (e.g., "/buy/browse/v1/item_summary/search")
            params: Query parameters for GET requests
            json_data: JSON body for POST/PUT requests
            form_data: Form data for requests requiring application/x-www-form-urlencoded
            headers: Additional headers to include
            token_override: Specific token to use instead of auto-managed tokens
            timeout: Request timeout (uses default if None)
            marketplace_id: eBay marketplace (EBAY_US, EBAY_GB, etc.)
            retry_on_auth_failure: Whether to retry with fresh token on auth failure
            
        Returns:
            Dict containing the parsed JSON response
            
        Raises:
            EbayAPIError: On API errors, network issues, or authentication failures
        """
        method = method.upper()
        timeout = timeout or self.default_timeout
        
        # Build full URL
        url = self._build_url(endpoint)
        
        # Get authentication token
        token = await self._get_token(token_override)
        
        # Build headers
        request_headers = self._build_headers(token, marketplace_id, headers)
        
        # Prepare request data
        request_kwargs: Dict[str, Any] = {
            "method": method,
            "url": url,
            "headers": request_headers,
            "timeout": timeout
        }
        
        if params:
            request_kwargs["params"] = params
        if json_data:
            request_kwargs["json"] = json_data
        if form_data:
            request_kwargs["data"] = form_data
            
        # Execute request with retries
        for attempt in range(self.max_retries + 1):
            try:
                # Rate limiting
                await self._rate_limit()
                
                # Log request
                logger.info(f"eBay API {method} {endpoint} (attempt {attempt + 1})")
                
                # Make request
                async with httpx.AsyncClient() as client:
                    response = await client.request(**request_kwargs)
                
                # Handle response
                return await self._handle_response(
                    response, endpoint, attempt, retry_on_auth_failure, token_override
                )
                
            except httpx.TimeoutException:
                if attempt == self.max_retries:
                    raise EbayAPIError(
                        f"Request timeout after {self.max_retries + 1} attempts",
                        endpoint=endpoint
                    )
                await self._backoff_delay(attempt)
                
            except httpx.RequestError as e:
                if attempt == self.max_retries:
                    raise EbayAPIError(
                        f"Network error: {str(e)}",
                        endpoint=endpoint
                    )
                await self._backoff_delay(attempt)
                
            except EbayAPIError as e:
                # Don't retry on auth errors if we're already retrying auth
                if e.status_code == 401 and retry_on_auth_failure and not token_override:
                    logger.warning(f"Auth failure on attempt {attempt + 1}, refreshing token...")
                    await self._invalidate_application_token()
                    token = await self._get_token(None)  # Get fresh token
                    request_headers = self._build_headers(token, marketplace_id, headers)
                    request_kwargs["headers"] = request_headers
                    continue
                
                # Retry on rate limit errors
                if e.status_code == 429:
                    delay = self._get_retry_delay(attempt, e.response_data)
                    logger.warning(f"Rate limited, waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
                    continue
                
                # Don't retry client errors (4xx) except auth and rate limit
                if e.status_code and 400 <= e.status_code < 500:
                    raise
                    
                # Retry server errors (5xx)
                if attempt < self.max_retries:
                    await self._backoff_delay(attempt)
                    continue
                    
                raise
        
        # This should never be reached due to the raise statements above
        raise EbayAPIError("Unexpected error: request loop completed without result")

    async def search_products(
        self,
        keyword: str,
        limit: int = 20,
        category_ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, str]] = None,
        sort: str = "price",
        marketplace_id: str = "EBAY_US"
    ) -> Dict[str, Any]:
        """
        Convenient method for searching eBay products.
        
        Args:
            keyword: Search term
            limit: Maximum results to return
            category_ids: eBay category IDs to search within
            filters: Additional filters (price range, condition, etc.)
            sort: Sort order (price, endingSoonest, newlyListed, etc.)
            marketplace_id: eBay marketplace
            
        Returns:
            Dict with search results and metadata
        """
        params = {
            "q": keyword,
            "limit": min(limit, 200),  # eBay max is 200
            "sort": sort
        }
        
        if category_ids:
            params["category_ids"] = ",".join(category_ids)
            
        if filters:
            # Convert filters dict to eBay filter format
            filter_strings = []
            for key, value in filters.items():
                filter_strings.append(f"{key}:{value}")
            params["filter"] = ",".join(filter_strings)
        
        response = await self.call_api(
            method="GET",
            endpoint="/buy/browse/v1/item_summary/search",
            params=params,
            marketplace_id=marketplace_id
        )
        
        # Add convenience metadata
        response["search_metadata"] = {
            "keyword": keyword,
            "marketplace": marketplace_id,
            "results_count": len(response.get("itemSummaries", [])),
            "total_results": response.get("total", 0)
        }
        
        return response

    async def get_item_details(
        self,
        item_ids: Union[str, List[str]],
        fieldgroups: Optional[List[str]] = None,
        marketplace_id: str = "EBAY_US"
    ) -> Dict[str, Any]:
        """
        Get detailed information for specific items.
        
        Args:
            item_ids: Single item ID or list of item IDs
            fieldgroups: Additional data to include (PRODUCT, EXTENDED, etc.)
            marketplace_id: eBay marketplace
            
        Returns:
            Dict with item details
        """
        if isinstance(item_ids, str):
            item_ids = [item_ids]
        
        params = {"item_ids": ",".join(item_ids)}
        if fieldgroups:
            params["fieldgroups"] = ",".join(fieldgroups)
        
        return await self.call_api(
            method="GET",
            endpoint="/buy/browse/v1/item/get_items",
            params=params,
            marketplace_id=marketplace_id
        )

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test eBay API connectivity and authentication.
        
        Returns:
            Dict with connection test results
        """
        test_results = {
            "timestamp": time.time(),
            "environment": self.base_url,
            "tests": []
        }
        
        # Test 1: Application Token
        try:
            token = await self._get_application_token()
            if token:
                test_results["tests"].append({
                    "test": "application_token",
                    "status": "success",
                    "message": "Application token obtained successfully",
                    "token_preview": f"{token[:15]}...{token[-8:]}"
                })
            else:
                test_results["tests"].append({
                    "test": "application_token",
                    "status": "failed",
                    "message": "Failed to obtain application token"
                })
        except Exception as e:
            test_results["tests"].append({
                "test": "application_token",
                "status": "error",
                "message": f"Error: {str(e)}"
            })
        
        # Test 2: Basic API Call
        try:
            response = await self.call_api(
                method="GET",
                endpoint="/buy/browse/v1/item_summary/search",
                params={"q": "test", "limit": 1}
            )
            if response:
                test_results["tests"].append({
                    "test": "api_call",
                    "status": "success",
                    "message": "API call successful",
                    "results_found": len(response.get("itemSummaries", []))
                })
        except Exception as e:
            test_results["tests"].append({
                "test": "api_call",
                "status": "error",
                "message": f"API call failed: {str(e)}"
            })
        
        # Overall status
        success_count = sum(1 for test in test_results["tests"] if test["status"] == "success")
        test_results["overall_status"] = "healthy" if success_count >= 2 else "issues"
        
        return test_results

    # Private methods for internal functionality
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith("/"):
            return urljoin(self.base_url, endpoint)
        return urljoin(self.base_url, f"/{endpoint}")
    
    def _build_headers(
        self,
        token: str,
        marketplace_id: str = "EBAY_US",
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Build request headers with authentication and eBay-specific headers."""
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if additional_headers:
            headers.update(additional_headers)
            
        return headers
    
    async def _get_token(self, token_override: Optional[str] = None) -> str:
        """Get appropriate authentication token."""
        if token_override:
            return token_override
            
        # Try application token first
        app_token = await self._get_application_token()
        if app_token:
            return app_token
            
        # Fall back to environment OAuth token
        oauth_token = os.getenv("EBAY_OAUTH_TOKEN") or os.getenv("EBAY_USER_TOKEN")
        if oauth_token:
            return oauth_token
            
        raise EbayAPIError("No valid eBay authentication token available")
    
    async def _get_application_token(self) -> Optional[str]:
        """Get or refresh eBay application token using Client Credentials flow."""
        # Check cache first
        if self._is_application_token_valid():
            return self._application_token_cache
            
        if not self.client_id or not self.client_secret:
            logger.error("CRITICAL: eBay client credentials not configured. Make sure EBAY_CLIENT_ID and EBAY_CLIENT_SECRET are set in your environment.")
            return None
            
        try:
            token_data = await self._request_application_token()
            if token_data:
                self._application_token_cache = token_data["access_token"]
                expires_in = token_data.get("expires_in", 7200)  # Default 2 hours
                self._application_token_expires_at = time.time() + expires_in
                logger.info("Successfully obtained eBay application token")
                return self._application_token_cache
        except Exception as e:
            logger.error(f"CRITICAL: An exception occurred while trying to get the eBay application token: {e}")
            
        return None
    
    def _is_application_token_valid(self) -> bool:
        """Check if cached application token is still valid."""
        if not self._application_token_cache:
            return False
        # Add 5-minute buffer before expiration
        return time.time() < (self._application_token_expires_at - 300)
    
    async def _request_application_token(self) -> Optional[Dict[str, Any]]:
        """Request new application token from eBay."""
        import base64

        logger.info(f"Attempting to request eBay application token. Client ID loaded: {bool(self.client_id)}")

        if not self.client_id or not self.client_secret:
            logger.error("CRITICAL: Cannot request token because EBAY_CLIENT_ID or EBAY_CLIENT_SECRET are missing.")
            return None

        # Prepare authentication
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

        url = urljoin(self.base_url, "/identity/v1/oauth2/token")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, data=data, timeout=15)

            if response.status_code == 200:
                logger.info("Successfully received token from eBay.")
                return response.json()
            else:
                logger.error(f"CRITICAL: eBay token request failed with status {response.status_code}. Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"CRITICAL: An unexpected error occurred during the httpx request to eBay: {e}")
            return None
    
    async def _invalidate_application_token(self) -> None:
        """Invalidate cached application token to force refresh."""
        self._application_token_cache = None
        self._application_token_expires_at = 0.0
    
    async def _handle_response(
        self,
        response: httpx.Response,
        endpoint: str,
        attempt: int,
        retry_on_auth_failure: bool,
        token_override: Optional[str]
    ) -> Dict[str, Any]:
        """Handle HTTP response and parse JSON."""
        # Log response
        logger.info(f"eBay API response: {response.status_code} for {endpoint}")
        
        # Success
        if response.is_success:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"raw_response": response.text}
        
        # Parse error response
        try:
            error_data = response.json()
        except json.JSONDecodeError:
            error_data = {"raw_error": response.text}
        
        # Create detailed error
        error_msg = f"eBay API error {response.status_code}"
        if "errors" in error_data:
            error_details = error_data["errors"][0] if error_data["errors"] else {}
            error_msg += f": {error_details.get('message', 'Unknown error')}"
        
        raise EbayAPIError(
            message=error_msg,
            status_code=response.status_code,
            response_data=error_data,
            endpoint=endpoint
        )
    
    async def _rate_limit(self) -> None:
        """Implement basic rate limiting."""
        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        self._last_request_time = time.time()
    
    async def _backoff_delay(self, attempt: int) -> None:
        """Exponential backoff delay for retries."""
        delay = self.rate_limit_delay * (2 ** attempt)
        await asyncio.sleep(delay)
    
    def _get_retry_delay(self, attempt: int, response_data: Dict[str, Any]) -> float:
        """Calculate retry delay for rate limiting."""
        # Check for Retry-After header info in response
        if isinstance(response_data, dict) and "errors" in response_data:
            for error in response_data["errors"]:
                if "parameters" in error:
                    for param in error["parameters"]:
                        if param.get("name") == "RateLimit-Reset":
                            try:
                                return float(param["value"])
                            except (ValueError, TypeError):
                                pass
        
        # Default exponential backoff
        return min(60, self.rate_limit_delay * (2 ** attempt))

# Global instance for easy usage
ebay_client = EbayAPIClient() 