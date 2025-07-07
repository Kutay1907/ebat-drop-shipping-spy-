from datetime import datetime
from typing import Optional
import os, asyncio
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .models import UserToken
from .database import async_session

EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"

async def save_token(session: AsyncSession, user_id: str, data: dict) -> UserToken:
    """Save or update token row for user."""
    stmt = select(UserToken).where(UserToken.user_id == user_id)
    result = await session.exec(stmt)
    existing: Optional[UserToken] = result.one_or_none()
    token = UserToken.from_token_response(user_id, data)
    if existing:
        existing.access_token = token.access_token
        existing.refresh_token = token.refresh_token
        existing.expires_at = token.expires_at
        await session.commit()
        return existing
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token

async def _refresh_token(refresh_token: str) -> dict:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "https://api.ebay.com/oauth/api_scope",
    }
    auth = (
        os.getenv("EBAY_CLIENT_ID") or "",
        os.getenv("EBAY_CLIENT_SECRET") or "",
    )
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(EBAY_TOKEN_URL, data=data, auth=auth, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()

async def get_valid_access_token(session: AsyncSession, user_id: str) -> Optional[str]:
    stmt = select(UserToken).where(UserToken.user_id == user_id)
    result = await session.exec(stmt)
    token: Optional[UserToken] = result.one_or_none()
    if not token:
        return None
    if token.expires_at > datetime.utcnow():
        return token.access_token
    # need refresh
    data = await asyncio.to_thread(_refresh_token, token.refresh_token)
    await save_token(session, user_id, data)
    return data["access_token"] 