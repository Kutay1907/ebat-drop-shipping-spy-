from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List

from .. import crud
from ..database import get_db
from ..ebay_api_client import EbayAPIClient

router = APIRouter(prefix="/api/seller", tags=["seller"])

class ListingRequest(BaseModel):
    sku: str = Field(..., description="A unique Stock Keeping Unit for the item.")
    title: str = Field(..., description="The title of the listing.")
    description: str = Field(..., description="The HTML description of the item.")
    price: float = Field(..., gt=0, description="The price of the item.")
    quantity: int = Field(..., gt=0, description="The available quantity.")
    image_urls: List[str] = Field(..., description="A list of URLs for the product images.")
    category_id: str = Field(..., description="The eBay category ID for the item.")
    fulfillment_policy_id: str = Field(..., description="The ID of the fulfillment policy.")
    payment_policy_id: str = Field(..., description="The ID of the payment policy.")
    return_policy_id: str = Field(..., description="The ID of the return policy.")

@router.post("/listing")
async def create_listing(listing: ListingRequest, db: Session = Depends(get_db)):
    """Creates an inventory item and publishes it as a new listing on eBay."""
    user_id = 1  # Hardcoded for the default user

    client = EbayAPIClient()
    
    # 1. Create or update the inventory item
    inventory_item_data = {
        "availability": {"shipToLocationAvailability": {"quantity": listing.quantity}},
        "condition": "NEW",
        "product": {
            "title": listing.title,
            "description": listing.description,
            "imageUrls": listing.image_urls,
        }
    }
    try:
        await client.create_or_replace_inventory_item(
            user_id=user_id, sku=listing.sku, item_data=inventory_item_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create inventory item: {str(e)}")

    # 2. Create the offer
    offer_data = {
        "sku": listing.sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "listingDescription": listing.description,
        "availableQuantity": listing.quantity,
        "categoryId": listing.category_id,
        "pricingSummary": {
            "price": {"currency": "USD", "value": str(listing.price)}
        },
        "listingPolicies": {
            "fulfillmentPolicyId": listing.fulfillment_policy_id,
            "paymentPolicyId": listing.payment_policy_id,
            "returnPolicyId": listing.return_policy_id,
        }
    }
    try:
        offer_response = await client.create_offer(user_id=user_id, offer_data=offer_data)
        offer_id = offer_response.get("offerId")
        if not offer_id:
            raise HTTPException(status_code=500, detail="Failed to retrieve offerId from eBay.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create offer: {str(e)}")

    # 3. Publish the offer
    try:
        listing_id = await client.publish_offer(user_id=user_id, offer_id=offer_id)
        if not listing_id:
            raise HTTPException(status_code=500, detail="Failed to publish offer.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish listing: {str(e)}")

    return {"listing_id": listing_id, "message": "Listing published successfully."} 