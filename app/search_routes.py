from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timezone
from fastapi import APIRouter, Query, HTTPException
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

from app.ebay_api_client import EbayAPIClient
ebay_client = EbayAPIClient()

class ItemCondition(str, Enum):
    """Item condition filters."""
    NEW = "1000"
    USED = "3000"
    CERTIFIED_REFURBISHED = "2000"
    SELLER_REFURBISHED = "2500"
    FOR_PARTS_OR_NOT_WORKING = "7000"

class SortOrder(str, Enum):
    """Sort order options."""
    BEST_MATCH = "bestMatch"
    PRICE_ASC = "price"
    PRICE_DESC = "-price"
    NEWLY_LISTED = "newlyListed"
    ENDING_SOONEST = "endingSoonest"

def determine_listing_type(buying_options: List[str]) -> str:
    """Determine listing type from buying options."""
    if "AUCTION" in buying_options:
        return "AUCTION"
    elif "FIXED_PRICE" in buying_options or "BUY_IT_NOW" in buying_options:
        return "BUY_IT_NOW"
    else:
        return "UNKNOWN"

@router.get("/search")
async def search_products(
    keyword: str = Query(..., min_length=1, max_length=100, description="Search keyword"),
    limit: int = Query(20, ge=1, le=200, description="Number of results to return"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    condition: Optional[ItemCondition] = Query(None, description="Item condition filter"),
    sort: SortOrder = Query(SortOrder.BEST_MATCH, description="Sort order"),
    buy_it_now_only: bool = Query(False, description="Show only Buy It Now items"),
    free_shipping_only: bool = Query(False, description="Show only items with free shipping"),
    marketplace: str = Query("EBAY_US", description="eBay marketplace"),
    min_feedback_score: Optional[int] = Query(None, ge=0, description="Minimum seller feedback score"),
    top_rated_sellers_only: bool = Query(False, description="Show only top-rated sellers"),
    fast_n_free: bool = Query(False, description="Items with Fast 'N Free shipping"),
    charity_ids: Optional[str] = Query(None, description="Comma-separated charity IDs"),
    exclude_categories: Optional[str] = Query(None, description="Comma-separated category IDs to exclude")
) -> Dict[str, Any]:
    """
    Enhanced eBay product search with proper filtering, item links, and available data.
    """
    try:
        # Build eBay API compatible filters
        filters = []
        
        # Price filters - eBay format: price:[min..max]
        if min_price is not None or max_price is not None:
            price_filter = "price:["
            price_filter += str(min_price) if min_price is not None else ""
            price_filter += ".."
            price_filter += str(max_price) if max_price is not None else ""
            price_filter += "]"
            filters.append(price_filter)
        
        # Condition filter
        if condition:
            filters.append(f"conditionIds:{{{condition.value}}}")
        
        # Delivery options
        if free_shipping_only:
            filters.append("deliveryOptions:{FreeShipping}")
        
        if fast_n_free:
            filters.append("deliveryOptions:{FastAndFree}")
        
        # Buying options
        if buy_it_now_only:
            filters.append("buyingOptions:{FIXED_PRICE}")
        
        # Seller filters
        if min_feedback_score is not None:
            filters.append(f"minFeedbackScore:{min_feedback_score}")
            
        if top_rated_sellers_only:
            filters.append("sellerTypes:{TopRated}")
        
        # Exclude categories
        if exclude_categories:
            excluded_cats = [cat.strip() for cat in exclude_categories.split(",")]
            for cat in excluded_cats:
                filters.append(f"excludeCategoryIds:{cat}")
        
        # Call eBay API with proper parameters
        params = {
            "q": keyword,
            "limit": limit,
            "sort": sort.value
        }
        
        # Add filters if any
        if filters:
            params["filter"] = " AND ".join(filters)
        
        # Use the ebay_client to search for products
        results = await ebay_client.call_api(
            method='GET',
            endpoint='/buy/browse/v1/item_summary/search',
            params=params
        )
        
        # Process and enhance the results
        enhanced_results = []
        
        for item in results.get("itemSummaries", []):
            # Extract price for filtering
            price_value = float(item.get("price", {}).get("value", 0))
            
            # Apply price filters
            if min_price is not None and price_value < min_price:
                continue
            if max_price is not None and price_value > max_price:
                continue
                
            # Extract seller info
            seller = item.get("seller", {})
            seller_feedback_score = seller.get("feedbackScore", 0)
            
            # Apply seller feedback filter
            if min_feedback_score is not None and seller_feedback_score < min_feedback_score:
                continue
            
            # Process the item
            processed_item = {
                "itemId": item.get("itemId"),
                "title": item.get("title"),
                "price": item.get("price"),
                "image_url": item.get("image", {}).get("imageUrl"),
                "item_web_url": item.get("itemWebUrl"),
                "condition": item.get("condition"),
                "listing_type": determine_listing_type(item.get("buyingOptions", [])),
                "free_shipping": any(opt.get("shippingCost", {}).get("value", "0") == "0.0" 
                                   for opt in item.get("shippingOptions", [])),
                "watch_count": item.get("watchCount", 0),
                "bid_count": item.get("bidCount", 0),
                "seller": {
                    "username": seller.get("username"),
                    "feedbackScore": seller_feedback_score,
                    "feedbackPercentage": seller.get("feedbackPercentage"),
                    "topRatedSeller": seller.get("topRatedSeller", False)
                }
            }
            
            enhanced_results.append(processed_item)
        
        return {
            "results": enhanced_results,
            "total_found": results.get("total", 0),
            "search_metadata": {
                "keyword": keyword,
                "marketplace": marketplace,
                "filters_applied": filters
            }
        }
        
    except Exception as e:
        logger.error(f"Error in search_products: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Search failed", "message": str(e)}
        ) 