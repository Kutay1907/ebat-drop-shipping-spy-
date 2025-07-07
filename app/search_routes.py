from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os, asyncio
from typing import Dict, Any

from app.ebay_client import ebay_keyword_search
from app.database import get_session
from app.token_service import get_valid_access_token
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api", tags=["search"])

class SearchRequest(BaseModel):
    keyword: str
    token: str | None = None  # optional if provided via env

@router.post("/search")
async def search_products(payload: SearchRequest, user_id: str | None = None, session: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    keyword = payload.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword is required")

    token = payload.token or await get_valid_access_token(session, user_id or "anonymous") or os.getenv("EBAY_OAUTH_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="OAuth token missing")

    try:
        results = await ebay_keyword_search(keyword, token)
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) 