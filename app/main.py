import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from urllib.parse import urlencode
import httpx
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta

from app.search_routes import router as search_router
from app.debug_routes import router as debug_router
from app.favorites_routes import router as favorites_router
from app.listing_routes import router as listing_router
from .database import engine, Base, get_db
from . import crud, models, security
from .ebay_oauth_service import ebay_oauth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
app.include_router(listing_router)

# --- eBay OAuth Routes ---

@app.get("/debug/oauth-url", tags=["debug"])
async def debug_oauth_url():
    """
    Debug endpoint to inspect the OAuth URL generation.
    This helps diagnose parameter issues with eBay OAuth.
    """
    try:
        # Check environment variables
        client_id = os.getenv("EBAY_CLIENT_ID")
        client_secret = os.getenv("EBAY_CLIENT_SECRET")
        redirect_uri = os.getenv("EBAY_REDIRECT_URI")
        encryption_key = os.getenv("ENCRYPTION_KEY")

        logger.info(f"Debug OAuth URL - Client ID: {client_id[:10] if client_id else 'None'}...")
        logger.info(f"Debug OAuth URL - Redirect URI: {redirect_uri}")

        # Generate the auth URL
        auth_url = ebay_oauth.get_authorization_url()

        return {
            "status": "success",
            "environment_check": {
                "client_id": "SET" if client_id else "NOT_SET",
                "client_secret": "SET" if client_secret else "NOT_SET",
                "redirect_uri": "SET" if redirect_uri else "NOT_SET",
                "encryption_key": "SET" if encryption_key else "NOT_SET"
            },
            "credentials_preview": {
                "client_id": f"{client_id[:10]}..." if client_id else None,
                "redirect_uri": redirect_uri
            },
            "generated_url": auth_url,
            "url_length": len(auth_url) if auth_url else 0,
            "scopes_count": len(ebay_oauth.scopes)
        }

    except Exception as e:
        logger.error(f"Debug OAuth URL error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "environment_check": {
                "client_id": "SET" if os.getenv("EBAY_CLIENT_ID") else "NOT_SET",
                "client_secret": "SET" if os.getenv("EBAY_CLIENT_SECRET") else "NOT_SET",
                "redirect_uri": "SET" if os.getenv("EBAY_REDIRECT_URI") else "NOT_SET",
                "encryption_key": "SET" if os.getenv("ENCRYPTION_KEY") else "NOT_SET"
            }
        }

@app.get("/connect/ebay", tags=["authentication"])
async def connect_ebay():
    """
    Redirect users to eBay OAuth consent page to connect their account.
    This is the main entry point for eBay authentication.
    """
    try:
        auth_url = ebay_oauth.get_authorization_url()
        logger.info(f"Redirecting user to eBay OAuth consent page: {auth_url[:100]}...")
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        logger.error(f"OAuth configuration error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"eBay OAuth not properly configured: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in connect_ebay: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initiate eBay connection"
        )

@app.get("/auth/ebay/login", tags=["authentication"])
async def ebay_login():
    """
    Alternative route that redirects to eBay's consent page.
    Maintained for backward compatibility.
    """
    return await connect_ebay()

@app.get("/auth/ebay/callback", tags=["authentication"])
async def auth_ebay_callback(
    code: str = Query(..., description="The authorization code from eBay"),
    state: str = Query(None, description="State parameter for CSRF protection"),
    db: Session = Depends(get_db)
):
    """
    Handle the callback from eBay OAuth consent page.
    Exchange authorization code for access and refresh tokens.
    """
    logger.info("Received eBay OAuth callback")

    try:
        # Exchange code for tokens
        token_data = await ebay_oauth.exchange_code_for_tokens(code)

        # Create or get user (in production, get user from session/JWT)
        user_email = "default_seller@example.com"
        db_user = crud.get_user_by_email(db, email=user_email)
        if not db_user:
            db_user = crud.create_user(db, email=user_email)
            logger.info(f"Created new user: {user_email}")

        if not db_user:
            raise HTTPException(
                status_code=500,
                detail="Could not create or find user account"
            )

        # Store encrypted tokens using the OAuth service
        ebay_oauth.store_user_tokens(db, db_user.id, token_data)

        logger.info(f"Successfully connected eBay account for user: {user_email}")
        return RedirectResponse(url="/?auth_status=success")

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to complete eBay authentication: {str(e)}"
        )

@app.get("/auth/ebay/status", tags=["authentication"])
async def auth_status(db: Session = Depends(get_db)):
    """
    Check the authentication status of the user.
    Returns connection status and token validity information.
    """
    try:
        user_id = 1  # In production, get from session/JWT

        is_connected = ebay_oauth.is_user_connected(db, user_id)
        if not is_connected:
            return {
                "is_connected": False,
                "needs_refresh": False,
                "message": "eBay account not connected"
            }

        # Check if token needs refresh
        needs_refresh = ebay_oauth.is_token_expired(db, user_id)

        # Get token expiration info
        token_record = ebay_oauth.get_stored_token(db, user_id)
        expires_at = token_record.access_token_expires_at.isoformat() if token_record else None

        return {
            "is_connected": True,
            "needs_refresh": needs_refresh,
            "expires_at": expires_at,
            "message": "eBay account connected successfully"
        }

    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check authentication status"
        )

@app.get("/auth/ebay/token", tags=["authentication"])
async def get_valid_token(db: Session = Depends(get_db)):
    """
    Get a valid access token for the user, refreshing if necessary.
    This endpoint can be used by other services to get authenticated tokens.
    """
    try:
        user_id = 1  # In production, get from session/JWT

        access_token = await ebay_oauth.get_valid_access_token(db, user_id)
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="No valid eBay authentication available. Please connect your account."
            )

        return {
            "access_token": access_token[:20] + "...",  # Only show partial token for security
            "token_type": "Bearer",
            "message": "Valid access token retrieved"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting valid token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve valid token"
        )

@app.post("/auth/ebay/disconnect", tags=["authentication"])
async def disconnect_ebay(db: Session = Depends(get_db)):
    """
    Disconnect the user's eBay account by removing stored tokens.
    """
    try:
        user_id = 1  # In production, get from session/JWT

        ebay_oauth.disconnect_user(db, user_id)

        return {
            "success": True,
            "message": "eBay account disconnected successfully"
        }

    except Exception as e:
        logger.error(f"Error disconnecting eBay account: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to disconnect eBay account"
        )

# --- Helper Functions for eBay API Usage ---

async def get_authenticated_ebay_client(db: Session, user_id: int):
    """
    Get an authenticated eBay API client for making authorized requests.

    Usage example:
        async with get_authenticated_ebay_client(db, user_id) as client:
            response = await client.get("/sell/inventory/v1/inventory_item")
    """
    access_token = await ebay_oauth.get_valid_access_token(db, user_id)
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="User not authenticated with eBay"
        )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    return httpx.AsyncClient(
        base_url="https://api.ebay.com",
        headers=headers,
        timeout=30
    )

@app.get("/api/ebay/inventory", tags=["ebay-api"])
async def get_user_inventory(db: Session = Depends(get_db)):
    """
    Example endpoint showing how to use authenticated eBay API calls.
    Get the user's inventory items from eBay.
    """
    try:
        user_id = 1  # In production, get from session/JWT

        async with await get_authenticated_ebay_client(db, user_id) as client:
            response = await client.get("/sell/inventory/v1/inventory_item")

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"eBay API error: {response.text}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching inventory: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch inventory from eBay"
        )

@app.get("/api/ebay/orders", tags=["ebay-api"])
async def get_user_orders(db: Session = Depends(get_db)):
    """
    Example endpoint showing how to get user's orders from eBay.
    """
    try:
        user_id = 1  # In production, get from session/JWT

        async with await get_authenticated_ebay_client(db, user_id) as client:
            response = await client.get("/sell/fulfillment/v1/order")

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"eBay API error: {response.text}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch orders from eBay"
        )

@app.get("/ebay/profile", tags=["ebay-api"])
async def get_ebay_profile(db: Session = Depends(get_db)):
    """
    Example route to make an authenticated eBay API call using stored access token.
    This demonstrates how to use the stored tokens to access eBay APIs.
    """
    try:
        user_id = 1  # In production, get from session/JWT

        async with await get_authenticated_ebay_client(db, user_id) as client:
            # Get user's account information
            response = await client.get("/sell/account/v1/account")

            if response.status_code == 200:
                return {
                    "status": "success",
                    "data": response.json(),
                    "message": "Successfully retrieved eBay profile"
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"eBay API error: {response.text}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching eBay profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch eBay profile"
        )

# --- Static Routes ---

@app.get("/", response_class=FileResponse)
async def read_root():
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        return HTMLResponse(
            content="<h1>Error: index.html not found</h1><p>Please make sure the static/index.html file exists.</p>",
            status_code=404
        )
    return FileResponse(index_path)

@app.get("/auth/success")
async def auth_success():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "ebay-dropshipping-spy",
        "ebay_oauth": {
            "client_id": "configured" if os.getenv("EBAY_CLIENT_ID") else "missing",
            "client_secret": "configured" if os.getenv("EBAY_CLIENT_SECRET") else "missing",
            "redirect_uri": "configured" if os.getenv("EBAY_REDIRECT_URI") else "missing",
            "encryption_key": "configured" if os.getenv("ENCRYPTION_KEY") else "missing"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )