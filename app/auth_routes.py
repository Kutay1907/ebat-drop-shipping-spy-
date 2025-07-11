import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import urlencode
import httpx

from .. import crud
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["authentication"])

CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("EBAY_REDIRECT_URI")

@router.get("/login")
async def ebay_login():
    """Redirects the user to eBay's consent page to start the OAuth2 flow."""
    if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        raise HTTPException(status_code=500, detail="OAuth credentials not configured on server.")
        
    scopes = [
        "https://api.ebay.com/oauth/api_scope/sell.inventory",
        "https://api.ebay.com/oauth/api_scope/sell.account",
        "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
    ]
    query_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(scopes),
        "prompt": "login"
    }
    ebay_auth_url = f"https://auth.ebay.com/oauth2/authorize?{urlencode(query_params)}"
    return RedirectResponse(url=ebay_auth_url)

@router.get("/callback")
async def ebay_callback(code: str = Query(...), db: Session = Depends(get_db)):
    """Handles the callback from eBay, exchanges the code for tokens, and stores them."""
    token_url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    
    async with httpx.AsyncClient() as client:
        auth = (CLIENT_ID, CLIENT_SECRET)
        response = await client.post(token_url, headers=headers, data=data, auth=auth)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to get token from eBay: {response.text}")
    
    token_data = response.json()

    # For now, create/use a default user.
    user_email = "default_seller@example.com"
    db_user = crud.get_user_by_email(db, email=user_email)
    if not db_user:
        db_user = crud.create_user(db, email=user_email)

    crud.update_or_create_token(db, user_id=db_user.id, token_data=token_data)

    return RedirectResponse(url="/?auth_status=success")

@router.get("/status")
async def auth_status(db: Session = Depends(get_db)):
    """Checks if the default user has a valid token."""
    # Using default user_id=1 for this simple case
    token = crud.get_token_for_user(db, user_id=1)
    is_connected = token is not None
    return {"is_connected": is_connected} 