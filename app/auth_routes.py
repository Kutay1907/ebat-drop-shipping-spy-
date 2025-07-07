from fastapi import APIRouter, Request, HTTPException
import requests
import os

router = APIRouter(prefix="/auth", tags=["auth"])

EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_AUTH_URL = "https://auth.ebay.com/oauth2/authorize"


def _post_token(data: dict) -> dict:
    """Helper to post to eBay token endpoint and return JSON or raise."""
    auth = (
        os.getenv("EBAY_CLIENT_ID") or "",
        os.getenv("EBAY_CLIENT_SECRET") or "",
    )
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(EBAY_TOKEN_URL, data=data, auth=auth, headers=headers, timeout=15)
    if not response.ok:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/callback")
def oauth_callback(request: Request, code: str):
    """eBay OAuth callback – exchange `code` for access & refresh tokens."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": os.getenv("EBAY_REDIRECT_URI"),
    }
    return _post_token(data)


@router.get("/refresh")
def refresh_token(refresh_token: str):
    """Refresh an existing eBay OAuth token."""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "https://api.ebay.com/oauth/api_scope",
    }
    return _post_token(data)


@router.get("/login")
def login():
    """Redirect user to eBay OAuth consent screen."""
    client_id = os.getenv("EBAY_CLIENT_ID")
    redirect_uri = os.getenv("EBAY_REDIRECT_URI")
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=500, detail="EBAY_CLIENT_ID/EBAY_REDIRECT_URI not configured")

    scope = "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.item.bulk https://api.ebay.com/oauth/api_scope/buy.marketplace.insights"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
    }
    from urllib.parse import urlencode
    auth_url = f"{EBAY_AUTH_URL}?{urlencode(params)}"
    from fastapi.responses import RedirectResponse
    return RedirectResponse(auth_url) 