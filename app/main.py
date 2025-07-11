import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from urllib.parse import urlencode
import httpx
from sqlalchemy.orm import Session

from app.search_routes import router as search_router
from app.debug_routes import router as debug_router
from app.favorites_routes import router as favorites_router
# from app.auth_routes import router as auth_router - no longer needed
from app.listing_routes import router as listing_router
from .database import engine, Base, get_db
from . import crud, models

# Create database tables
Base.metadata.create_all(bind=engine)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"

app = FastAPI(
    title="eBay Dropshipping Spy & Seller Tool",
    description="A powerful tool for eBay product research, analysis, and seller management.",
    version="2.0.0"
)

STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(search_router)
app.include_router(debug_router)
app.include_router(favorites_router)
# app.include_router(auth_router) - no longer needed
app.include_router(listing_router)

# --- Start of Moved Auth Routes ---

CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("EBAY_REDIRECT_URI")

@app.get("/auth/ebay/login", tags=["authentication"])
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

@app.get("/auth/ebay/callback", tags=["authentication"])
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
        if not CLIENT_ID or not CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="OAuth client credentials not configured on server.")
        
        auth = (CLIENT_ID, CLIENT_SECRET)
        response = await client.post(token_url, headers=headers, data=data, auth=auth)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to get token from eBay: {response.text}")
    
    token_data = response.json()

    user_email = "default_seller@example.com"
    db_user = crud.get_user_by_email(db, email=user_email)
    if not db_user:
        # Create the user, but then refetch it to ensure we have a clean session object
        crud.create_user(db, email=user_email)
        db_user = crud.get_user_by_email(db, email=user_email)

    if not db_user or not db_user.id:
        raise HTTPException(status_code=500, detail="Could not create or find a user.")

    crud.update_or_create_token(db, user_id=db_user.id, token_data=token_data)

    return RedirectResponse(url="/?auth_status=success")

@app.get("/auth/ebay/status", tags=["authentication"])
async def auth_status(db: Session = Depends(get_db)):
    """Checks if the default user has a valid token."""
    # Using default user_id=1 for this simple case
    token = crud.get_token_for_user(db, user_id=1)
    is_connected = token is not None
    return {"is_connected": is_connected}

# --- End of Moved Auth Routes ---

@app.get("/", response_class=FileResponse)
async def read_root():
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        return HTMLResponse(content="<h1>Error: index.html not found</h1><p>Please make sure the static/index.html file exists.</p>", status_code=404)
    return FileResponse(index_path)

@app.get("/auth/success")
async def auth_success():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ebay-dropshipping-spy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )