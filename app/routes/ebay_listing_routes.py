"""
eBay Listing Routes Module
=========================

API routes for creating and managing eBay listings using the eBay Sell API.
Handles inventory creation, listing management, and automated product listing.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.ebay_api_client import get_user_ebay_client
from app.ebay_oauth_service import EbayOAuthService
from app import crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ebay", tags=["ebay-listing"])

# Initialize OAuth service
ebay_oauth = EbayOAuthService()

class EbayListingRequest(BaseModel):
    """Request model for creating eBay listings."""
    title: str
    description: str
    price: float
    quantity: int = 1
    category_id: str = "182094"  # Default to "Cell Phones & Accessories"
    condition: str = "NEW"
    image_urls: List[str] = []
    item_specifics: Dict[str, str] = {}
    listing_duration: str = "GTC"  # Good Till Cancelled
    return_policy: Optional[str] = None
    shipping_policy: Optional[str] = None
    payment_policy: Optional[str] = None
    
    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Title is required")
        if len(v) > 80:
            raise ValueError("Title must be 80 characters or less")
        return v.strip()
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        if v > 99999.99:
            raise ValueError("Price too high")
        return round(v, 2)
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError("Quantity must be at least 1")
        if v > 1000:
            raise ValueError("Quantity too high")
        return v
    
    @validator('image_urls')
    def validate_images(cls, v):
        if len(v) > 12:
            raise ValueError("Maximum 12 images allowed")
        # Basic URL validation
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid image URL: {url}")
        return v

class EbayListingResponse(BaseModel):
    """Response model for eBay listing creation."""
    success: bool
    listing_id: Optional[str] = None
    sku: Optional[str] = None
    ebay_item_id: Optional[str] = None
    listing_url: Optional[str] = None
    message: str
    errors: List[str] = []

@router.post("/listing", response_model=EbayListingResponse)
async def create_ebay_listing(
    request: EbayListingRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new eBay listing using the Sell Inventory API.
    
    This endpoint:
    1. Creates an inventory item
    2. Creates an offer for the item
    3. Publishes the listing to eBay
    
    Args:
        request: Listing creation request with all product details
        
    Returns:
        Listing creation result with eBay item ID and listing URL
    """
    try:
        user_id = 1  # In production, get from session/JWT
        
        # Check if user is connected to eBay
        if not ebay_oauth.is_user_connected(db, user_id):
            raise HTTPException(
                status_code=401,
                detail="eBay account not connected. Please connect your eBay account first."
            )
        
        logger.info(f"Creating eBay listing for user {user_id}: {request.title}")
        
        # Get authenticated eBay client
        client = get_user_ebay_client(user_id)
        
        # Generate unique SKU
        sku = f"AMZ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Step 1: Create Inventory Item
        inventory_item = await create_inventory_item(client, sku, request)
        
        # Step 2: Create Offer
        offer_response = await create_offer(client, sku, request)
        
        # Step 3: Publish Listing
        offer_id = offer_response.get('offerId')
        if not offer_id:
            raise Exception("No offer ID returned from eBay")
        publish_response = await publish_listing(client, offer_id)
        
        # Extract listing details
        listing_id = offer_response.get('offerId')
        ebay_item_id = publish_response.get('listingId')
        listing_url = f"https://www.ebay.com/itm/{ebay_item_id}" if ebay_item_id else None
        
        logger.info(f"Successfully created eBay listing: {ebay_item_id}")
        
        return EbayListingResponse(
            success=True,
            listing_id=listing_id,
            sku=sku,
            ebay_item_id=ebay_item_id,
            listing_url=listing_url,
            message=f"Successfully created eBay listing: {request.title}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating eBay listing: {str(e)}")
        return EbayListingResponse(
            success=False,
            message="Failed to create eBay listing",
            errors=[str(e)]
        )

async def create_inventory_item(client, sku: str, request: EbayListingRequest) -> Dict[str, Any]:
    """Create an inventory item using eBay Sell Inventory API."""
    
    # Prepare product details  
    product_data: Dict[str, Any] = {
        "product": {
            "title": request.title,
            "description": request.description,
            "aspects": request.item_specifics,
            "brand": request.item_specifics.get("Brand", "Unbranded"),
            "imageUrls": request.image_urls[:12]  # Limit to 12 images
        }
    }
    
    # Add condition
    if request.condition:
        product_data["condition"] = request.condition
        product_data["conditionDescription"] = "New item in original packaging"
    
    # Create inventory item
    response = await client.call_api(
        "PUT",
        f"/sell/inventory/v1/inventory_item/{sku}",
        json_data=product_data
    )
    
    logger.info(f"Created inventory item with SKU: {sku}")
    return response

async def create_offer(client, sku: str, request: EbayListingRequest) -> Dict[str, Any]:
    """Create an offer for the inventory item."""
    
    # Prepare offer data
    offer_data = {
        "sku": sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "availableQuantity": request.quantity,
        "categoryId": request.category_id,
        "listingDescription": request.description,
        "listingPolicies": {
            "fulfillmentPolicyId": request.shipping_policy or await get_default_shipping_policy(client),
            "paymentPolicyId": request.payment_policy or await get_default_payment_policy(client),
            "returnPolicyId": request.return_policy or await get_default_return_policy(client)
        },
        "pricingSummary": {
            "price": {
                "value": str(request.price),
                "currency": "USD"
            }
        },
        "quantityLimitPerBuyer": min(request.quantity, 10),
        "listingDuration": request.listing_duration
    }
    
    # Create offer
    response = await client.call_api(
        "POST",
        "/sell/inventory/v1/offer",
        json_data=offer_data
    )
    
    logger.info(f"Created offer for SKU: {sku}")
    return response

async def publish_listing(client, offer_id: str) -> Dict[str, Any]:
    """Publish the offer to eBay."""
    
    publish_data = {
        "offerId": offer_id
    }
    
    response = await client.call_api(
        "POST",
        f"/sell/inventory/v1/offer/{offer_id}/publish",
        json_data=publish_data
    )
    
    logger.info(f"Published listing for offer: {offer_id}")
    return response

async def get_default_shipping_policy(client) -> str:
    """Get or create a default shipping policy."""
    try:
        # Try to get existing policies
        response = await client.call_api("GET", "/sell/account/v1/fulfillment_policy")
        policies = response.get("fulfillmentPolicies", [])
        
        if policies:
            return policies[0]["fulfillmentPolicyId"]
        
        # Create a default shipping policy if none exists
        policy_data = {
            "name": "Standard Shipping",
            "description": "Standard shipping policy",
            "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
            "handlingTime": {"value": 1, "unit": "DAY"},
            "shippingOptions": [{
                "costType": "FLAT_RATE",
                "shippingServices": [{
                    "sortOrder": 1,
                    "shippingServiceCode": "USPSGround",
                    "shippingCost": {"value": "5.99", "currency": "USD"}
                }]
            }]
        }
        
        response = await client.call_api(
            "POST",
            "/sell/account/v1/fulfillment_policy",
            json_data=policy_data
        )
        
        return response["fulfillmentPolicyId"]
        
    except Exception as e:
        logger.warning(f"Could not get shipping policy: {e}")
        return "DEFAULT_SHIPPING_POLICY"

async def get_default_payment_policy(client) -> str:
    """Get or create a default payment policy."""
    try:
        response = await client.call_api("GET", "/sell/account/v1/payment_policy")
        policies = response.get("paymentPolicies", [])
        
        if policies:
            return policies[0]["paymentPolicyId"]
        
        # Create default payment policy
        policy_data = {
            "name": "Immediate Payment Required",
            "description": "Immediate payment required",
            "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
            "paymentMethods": [{"paymentMethodType": "PAYPAL"}],
            "immediatePay": True
        }
        
        response = await client.call_api(
            "POST",
            "/sell/account/v1/payment_policy",
            json_data=policy_data
        )
        
        return response["paymentPolicyId"]
        
    except Exception as e:
        logger.warning(f"Could not get payment policy: {e}")
        return "DEFAULT_PAYMENT_POLICY"

async def get_default_return_policy(client) -> str:
    """Get or create a default return policy."""
    try:
        response = await client.call_api("GET", "/sell/account/v1/return_policy")
        policies = response.get("returnPolicies", [])
        
        if policies:
            return policies[0]["returnPolicyId"]
        
        # Create default return policy
        policy_data = {
            "name": "30-Day Returns",
            "description": "30-day return policy",
            "categoryTypes": [{"name": "ALL_EXCLUDING_MOTORS_VEHICLES"}],
            "returnMethod": "REPLACEMENT",
            "returnPeriod": {"value": 30, "unit": "DAY"},
            "returnShippingCostPayer": "BUYER"
        }
        
        response = await client.call_api(
            "POST",
            "/sell/account/v1/return_policy",
            json_data=policy_data
        )
        
        return response["returnPolicyId"]
        
    except Exception as e:
        logger.warning(f"Could not get return policy: {e}")
        return "DEFAULT_RETURN_POLICY"

@router.get("/policies")
async def get_user_policies(db: Session = Depends(get_db)):
    """Get user's eBay business policies."""
    try:
        user_id = 1  # In production, get from session/JWT
        
        if not ebay_oauth.is_user_connected(db, user_id):
            raise HTTPException(
                status_code=401,
                detail="eBay account not connected"
            )
        
        client = get_user_ebay_client(user_id)
        
        # Get all policy types
        shipping_policies = await client.call_api("GET", "/sell/account/v1/fulfillment_policy")
        payment_policies = await client.call_api("GET", "/sell/account/v1/payment_policy")
        return_policies = await client.call_api("GET", "/sell/account/v1/return_policy")
        
        return {
            "shipping_policies": shipping_policies.get("fulfillmentPolicies", []),
            "payment_policies": payment_policies.get("paymentPolicies", []),
            "return_policies": return_policies.get("returnPolicies", [])
        }
        
    except Exception as e:
        logger.error(f"Error fetching policies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch eBay policies"
        )

@router.get("/categories")
async def get_ebay_categories():
    """Get common eBay categories for listing."""
    # Common categories for dropshipping
    categories = {
        "182094": "Cell Phones & Accessories",
        "293": "Consumer Electronics",
        "1281": "Jewelry & Watches", 
        "11450": "Clothing, Shoes & Accessories",
        "2984": "Sporting Goods",
        "11232": "Video Games & Consoles",
        "58058": "Health & Beauty",
        "26395": "Pet Supplies",
        "1249": "Video Games",
        "11233": "Video Game Accessories"
    }
    
    return {"categories": categories} 