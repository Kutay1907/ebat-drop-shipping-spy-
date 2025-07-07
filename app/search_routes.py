from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os, asyncio
from typing import Dict, Any

from ..ebay_client import ebay_keyword_search

router = APIRouter(prefix="/api", tags=["search"])

class SearchRequest(BaseModel):
    keyword: str
    token: str | None = None  # optional if provided via env

@router.post("/search")
async def search_products(payload: SearchRequest) -> Dict[str, Any]:
    keyword = payload.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword is required")

    token = payload.token or os.getenv("EBAY_OAUTH_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="OAuth token missing")

    try:
        results = await ebay_keyword_search(keyword, token)
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) 