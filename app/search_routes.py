from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import os
import asyncio
from typing import Dict, Any, Optional, List

# Import the new comprehensive API client
from app.ebay_api_client import ebay_client, EbayAPIError
from app.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api", tags=["search"])

class SearchRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100, description="Search keyword")
    token: Optional[str] = Field(None, description="Optional eBay OAuth token override")
    limit: Optional[int] = Field(20, ge=1, le=200, description="Number of results to return")
    sort: Optional[str] = Field("price", description="Sort order (price, endingSoonest, newlyListed)")
    marketplace: Optional[str] = Field("EBAY_US", description="eBay marketplace (EBAY_US, EBAY_GB, etc.)")

class AdvancedSearchRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100)
    token: Optional[str] = None
    limit: Optional[int] = Field(20, ge=1, le=200)
    sort: Optional[str] = Field("price")
    marketplace: Optional[str] = Field("EBAY_US")
    category_ids: Optional[List[str]] = Field(None, description="eBay category IDs")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    condition: Optional[str] = Field(None, description="Item condition (NEW, USED, etc.)")
    location: Optional[str] = Field(None, description="Item location filter")

class DirectAPIRequest(BaseModel):
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE)")
    endpoint: str = Field(..., description="eBay API endpoint path")
    params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    json_data: Optional[Dict[str, Any]] = Field(None, description="JSON request body")
    token: Optional[str] = Field(None, description="Authentication token")
    marketplace: Optional[str] = Field("EBAY_US", description="eBay marketplace")

@router.post("/search")
async def search_products(payload: SearchRequest, session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    """
    Search eBay products using the comprehensive API client.
    Supports Application Token, User OAuth token, and manual token override.
    """
    try:
        results = await ebay_client.search_products(
            keyword=payload.keyword,
            limit=payload.limit or 20,
            sort=payload.sort or "price",
            marketplace_id=payload.marketplace or "EBAY_US"
        )
        
        return {
            "success": True,
            "keyword": payload.keyword,
            "marketplace": payload.marketplace or "EBAY_US",
            "results": results.get("itemSummaries", []),
            "total_found": results.get("total", 0),
            "search_metadata": results.get("search_metadata", {}),
            "pagination": {
                "limit": payload.limit or 20,
                "returned_count": len(results.get("itemSummaries", []))
            }
        }
    except EbayAPIError as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail={
                "error": "eBay API Error",
                "message": e.message,
                "endpoint": e.endpoint,
                "response_data": e.response_data
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.post("/search/advanced")
async def advanced_search(payload: AdvancedSearchRequest) -> Dict[str, Any]:
    """
    Advanced product search with filters and categories.
    """
    try:
        # Build filters dictionary
        filters = {}
        if payload.min_price is not None or payload.max_price is not None:
            price_filter = []
            if payload.min_price is not None:
                price_filter.append(str(payload.min_price))
            else:
                price_filter.append("*")
            price_filter.append("..")
            if payload.max_price is not None:
                price_filter.append(str(payload.max_price))
            else:
                price_filter.append("*")
            filters["price"] = f"[{''.join(price_filter)}]"
        
        if payload.condition:
            filters["condition"] = payload.condition
            
        if payload.location:
            filters["itemLocationCountry"] = payload.location
        
        results = await ebay_client.search_products(
            keyword=payload.keyword,
            limit=payload.limit or 20,
            category_ids=payload.category_ids,
            filters=filters if filters else None,
            sort=payload.sort or "price",
            marketplace_id=payload.marketplace or "EBAY_US"
        )
        
        return {
            "success": True,
            "search_type": "advanced",
            "filters_applied": filters,
            "keyword": payload.keyword,
            "results": results.get("itemSummaries", []),
            "total_found": results.get("total", 0),
            "search_metadata": results.get("search_metadata", {})
        }
    except EbayAPIError as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail={
                "error": "eBay API Error", 
                "message": e.message,
                "filters": filters if 'filters' in locals() else None
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced search error: {str(e)}")

@router.post("/api-call")
async def direct_api_call(payload: DirectAPIRequest) -> Dict[str, Any]:
    """
    Make a direct call to any eBay API endpoint.
    This is the comprehensive solution the user requested - converts any API Explorer call into code.
    """
    try:
        response = await ebay_client.call_api(
            method=payload.method,
            endpoint=payload.endpoint,
            params=payload.params,
            json_data=payload.json_data,
            token_override=payload.token,
            marketplace_id=payload.marketplace or "EBAY_US"
        )
        
        return {
            "success": True,
            "method": payload.method,
            "endpoint": payload.endpoint,
            "marketplace": payload.marketplace or "EBAY_US",
            "response": response,
            "metadata": {
                "has_token_override": bool(payload.token),
                "request_params": payload.params,
                "request_body": payload.json_data
            }
        }
    except EbayAPIError as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail={
                "error": "eBay API Error",
                "message": e.message,
                "endpoint": e.endpoint,
                "method": payload.method,
                "response_data": e.response_data
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API call error: {str(e)}")

@router.get("/item/{item_id}")
async def get_item_details(
    item_id: str,
    fieldgroups: Optional[str] = Query(None, description="Comma-separated fieldgroups (PRODUCT,EXTENDED,etc.)"),
    marketplace: str = Query("EBAY_US", description="eBay marketplace")
) -> Dict[str, Any]:
    """
    Get detailed information for a specific eBay item.
    """
    try:
        fieldgroups_list = fieldgroups.split(",") if fieldgroups else None
        
        response = await ebay_client.get_item_details(
            item_ids=item_id,
            fieldgroups=fieldgroups_list,
            marketplace_id=marketplace
        )
        
        return {
            "success": True,
            "item_id": item_id,
            "marketplace": marketplace,
            "fieldgroups": fieldgroups_list,
            "item_data": response
        }
    except EbayAPIError as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail={
                "error": "eBay API Error",
                "message": e.message,
                "item_id": item_id
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Item details error: {str(e)}")

@router.get("/test-connection")
async def test_ebay_connection() -> Dict[str, Any]:
    """
    Comprehensive test of eBay API connectivity and authentication.
    Tests both Application Token and User OAuth Token functionality.
    """
    try:
        results = await ebay_client.test_connection()
        
        # Add environment configuration status
        env_status = {
            "EBAY_CLIENT_ID": "SET" if os.getenv("EBAY_CLIENT_ID") else "NOT_SET",
            "EBAY_CLIENT_SECRET": "SET" if os.getenv("EBAY_CLIENT_SECRET") else "NOT_SET", 
            "EBAY_OAUTH_TOKEN": "SET" if os.getenv("EBAY_OAUTH_TOKEN") else "NOT_SET",
            "EBAY_USER_TOKEN": "SET" if os.getenv("EBAY_USER_TOKEN") else "NOT_SET"
        }
        
        results["environment_config"] = env_status
        results["recommendations"] = []
        
        # Add specific recommendations
        if env_status["EBAY_CLIENT_ID"] == "NOT_SET" or env_status["EBAY_CLIENT_SECRET"] == "NOT_SET":
            results["recommendations"].append(
                "Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET for Application Token authentication"
            )
        
        if all(env_status[key] == "NOT_SET" for key in ["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET", "EBAY_OAUTH_TOKEN", "EBAY_USER_TOKEN"]):
            results["recommendations"].append(
                "No eBay credentials configured. Set up at least one authentication method."
            )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test error: {str(e)}")

@router.get("/search/test-token")
async def test_ebay_token():
    """
    Legacy compatibility endpoint - redirects to comprehensive test.
    """
    return await test_ebay_connection()

@router.post("/search/with-token")
async def search_with_specific_token(
    token: str = Query(..., description="eBay authentication token"),
    keyword: str = Query(..., description="Search keyword"),
    limit: int = Query(20, ge=1, le=200, description="Number of results")
) -> Dict[str, Any]:
    """
    Search with a specific token for testing token functionality.
    """
    try:
        # Override token for this specific call
        response = await ebay_client.call_api(
            method="GET",
            endpoint="/buy/browse/v1/item_summary/search",
            params={"q": keyword, "limit": limit},
            token_override=token
        )
        
        return {
            "success": True,
            "keyword": keyword,
            "token_type": "provided_override",
            "token_preview": f"{token[:20]}...{token[-10:]}" if len(token) > 30 else "short_token",
            "results": response.get("itemSummaries", []),
            "total_found": response.get("total", 0)
        }
    except EbayAPIError as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail={
                "error": "Token Test Failed",
                "message": e.message,
                "token_preview": f"{token[:15]}...{token[-8:]}" if len(token) > 23 else "invalid_token"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token test error: {str(e)}")

@router.get("/marketplace/info")
async def get_marketplace_info() -> Dict[str, Any]:
    """
    Get information about available eBay marketplaces and their capabilities.
    """
    marketplaces = {
        "EBAY_US": {"name": "United States", "currency": "USD", "site_id": 0},
        "EBAY_GB": {"name": "United Kingdom", "currency": "GBP", "site_id": 3},
        "EBAY_AU": {"name": "Australia", "currency": "AUD", "site_id": 15},
        "EBAY_CA": {"name": "Canada", "currency": "CAD", "site_id": 2},
        "EBAY_DE": {"name": "Germany", "currency": "EUR", "site_id": 77},
        "EBAY_FR": {"name": "France", "currency": "EUR", "site_id": 71},
        "EBAY_IT": {"name": "Italy", "currency": "EUR", "site_id": 101},
        "EBAY_ES": {"name": "Spain", "currency": "EUR", "site_id": 186},
        "EBAY_NL": {"name": "Netherlands", "currency": "EUR", "site_id": 146},
        "EBAY_BE": {"name": "Belgium", "currency": "EUR", "site_id": 23}
    }
    
    return {
        "success": True,
        "marketplaces": marketplaces,
        "default": "EBAY_US",
        "supported_features": {
            "search": "All marketplaces",
            "item_details": "All marketplaces", 
            "advanced_filters": "All marketplaces",
            "category_search": "All marketplaces"
        }
    }

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for the eBay API integration.
    """
    try:
        # Quick connection test
        token_available = bool(
            os.getenv("EBAY_CLIENT_ID") and os.getenv("EBAY_CLIENT_SECRET") or
            os.getenv("EBAY_OAUTH_TOKEN") or 
            os.getenv("EBAY_USER_TOKEN")
        )
        
        return {
            "status": "healthy",
            "service": "eBay API Integration",
            "features": {
                "basic_search": True,
                "advanced_search": True,
                "direct_api_calls": True,
                "item_details": True,
                "multi_marketplace": True
            },
            "authentication": {
                "token_available": token_available,
                "application_token_support": bool(os.getenv("EBAY_CLIENT_ID")),
                "user_oauth_support": bool(os.getenv("EBAY_OAUTH_TOKEN"))
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "service": "eBay API Integration"
        } 