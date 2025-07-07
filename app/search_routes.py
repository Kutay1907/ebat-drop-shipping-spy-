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
    Search eBay products using Application Token (no user login required).
    For product browsing, we use eBay's Client Credentials grant flow.
    """
    keyword = payload.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword is required")

    # Get Application Token (much simpler than User OAuth)
    token = payload.token or await ebay_token_service.get_application_token()
    
    if not token:
        raise HTTPException(
            status_code=500, 
            detail="Unable to obtain eBay API token. Check EBAY_CLIENT_ID and EBAY_CLIENT_SECRET configuration."
        )

    try:
        results = await ebay_keyword_search(keyword, token)
        return {
            "keyword": keyword,
            "token_type": "application",
            "results": results.get("results", []),
            "total_found": len(results.get("results", []))
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"eBay API error: {str(exc)}")

@router.get("/search/test-token")
async def test_ebay_token():
    """
    Test endpoint to verify eBay token generation is working
    """
    try:
        token = await ebay_token_service.get_application_token()
        if token:
            # Don't return the actual token for security
            return {
                "status": "success",
                "message": "eBay Application Token obtained successfully",
                "token_preview": f"{token[:10]}...{token[-4:]}",
                "token_length": len(token)
            }
        else:
            return {
                "status": "error",
                "message": "Failed to obtain eBay Application Token",
                "check": ["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token test failed: {str(e)}") 