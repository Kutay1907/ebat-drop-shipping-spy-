from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os, asyncio
from typing import Dict, Any, Optional

from ebay_client import ebay_keyword_search
from app.database import get_session
from app.ebay_token_service import ebay_token_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api", tags=["search"])

class SearchRequest(BaseModel):
    keyword: str
    token: Optional[str] = None  # optional override token

@router.post("/search")
async def search_products(payload: SearchRequest, session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    """
    Search eBay products using Application Token or User OAuth token.
    Priority: 1) Manual token 2) Application token 3) Environment OAuth token
    """
    keyword = payload.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword is required")

    token = None
    token_type = "unknown"
    
    # Priority 1: Manual token override
    if payload.token:
        token = payload.token
        token_type = "manual"
    
    # Priority 2: Application Token (preferred for product search)
    if not token:
        try:
            token = await ebay_token_service.get_application_token()
            if token:
                token_type = "application"
        except Exception as e:
            print(f"Application token failed: {e}")
    
    # Priority 3: User OAuth token from environment (fallback)
    if not token:
        token = os.getenv("EBAY_OAUTH_TOKEN") or os.getenv("EBAY_USER_TOKEN")
        if token:
            token_type = "user_oauth"
    
    if not token:
        raise HTTPException(
            status_code=500, 
            detail="No eBay token available. Set EBAY_CLIENT_ID + EBAY_CLIENT_SECRET for Application Token, or EBAY_OAUTH_TOKEN for User Token."
        )

    try:
        results = await ebay_keyword_search(keyword, token)
        return {
            "keyword": keyword,
            "token_type": token_type,
            "token_preview": f"{token[:20]}...{token[-10:]}" if len(token) > 30 else "short_token",
            "results": results.get("results", []),
            "total_found": len(results.get("results", []))
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"eBay API error: {str(exc)}")

@router.get("/search/test-token")
async def test_ebay_token():
    """
    Test endpoint to verify eBay token generation is working
    Tests both Application Token and User OAuth Token
    """
    results = {"tests": []}
    
    # Test 1: Application Token
    try:
        app_token = await ebay_token_service.get_application_token()
        if app_token:
            results["tests"].append({
                "type": "application_token",
                "status": "success",
                "message": "Application Token obtained successfully",
                "token_preview": f"{app_token[:15]}...{app_token[-8:]}",
                "token_length": len(app_token)
            })
        else:
            results["tests"].append({
                "type": "application_token", 
                "status": "failed",
                "message": "Application Token failed - check EBAY_CLIENT_ID and EBAY_CLIENT_SECRET"
            })
    except Exception as e:
        results["tests"].append({
            "type": "application_token",
            "status": "error", 
            "message": f"Application Token error: {str(e)}"
        })
    
    # Test 2: User OAuth Token from environment
    user_token = os.getenv("EBAY_OAUTH_TOKEN") or os.getenv("EBAY_USER_TOKEN")
    if user_token:
        results["tests"].append({
            "type": "user_oauth_token",
            "status": "success",
            "message": "User OAuth Token found in environment",
            "token_preview": f"{user_token[:20]}...{user_token[-10:]}",
            "token_length": len(user_token)
        })
    else:
        results["tests"].append({
            "type": "user_oauth_token",
            "status": "not_found",
            "message": "No User OAuth Token in environment (EBAY_OAUTH_TOKEN or EBAY_USER_TOKEN)"
        })
    
    # Overall status
    has_working_token = any(test["status"] == "success" for test in results["tests"])
    results["overall_status"] = "ready" if has_working_token else "needs_setup"
    results["recommendation"] = (
        "✅ Ready to search products!" if has_working_token 
        else "❌ Configure at least one token type to enable product search"
    )
    
    return results

@router.post("/search/with-token")
async def search_with_specific_token(token: str, keyword: str):
    """
    Direct search with a specific token (for testing specific tokens)
    """
    if not keyword.strip():
        raise HTTPException(status_code=400, detail="keyword is required")
    if not token.strip():
        raise HTTPException(status_code=400, detail="token is required")
        
    try:
        results = await ebay_keyword_search(keyword.strip(), token.strip())
        return {
            "keyword": keyword,
            "token_type": "provided",
            "token_preview": f"{token[:20]}...{token[-10:]}",
            "results": results.get("results", []),
            "total_found": len(results.get("results", []))
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"eBay API error with provided token: {str(exc)}") 