import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timezone
import sys
import os
import random

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi import APIRouter, HTTPException, Query, Depends
except ImportError:
    raise ImportError("FastAPI is required. Please install it with: pip install fastapi")

# Import the API client
try:
    from app.ebay_api_client import ebay_client, EbayAPIError
except ImportError:
    from ebay_api_client import ebay_client, EbayAPIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])

class SortOrder(str, Enum):
    """Available sort orders for eBay search."""
    BEST_MATCH = "bestMatch"
    PRICE_LOW_TO_HIGH = "price"
    PRICE_HIGH_TO_LOW = "-price"
    ENDING_SOONEST = "endingSoonest"
    NEWLY_LISTED = "newlyListed"
    DISTANCE_NEAREST = "distance"

class ItemCondition(str, Enum):
    """Available item conditions."""
    NEW = "1000"
    USED = "3000"
    CERTIFIED_REFURBISHED = "2000"
    SELLER_REFURBISHED = "2500"
    FOR_PARTS_OR_NOT_WORKING = "7000"

def prepare_search_keywords(keyword: str) -> str:
    """
    Prepare search keywords for optimal eBay results.
    """
    if not keyword:
        return keyword
    
    keyword = keyword.strip()
    
    # If already quoted, leave as is
    if keyword.startswith('"') and keyword.endswith('"'):
        return keyword
    
    # For multi-word searches, use quotes for better results
    words = keyword.split()
    if len(words) > 1:
        return f'"{keyword}"'
    
    return keyword

@router.get("/search")
async def search_products(
    keyword: str = Query(..., min_length=1, max_length=200, description="Search keyword"),
    limit: int = Query(50, ge=1, le=200, description="Number of results to return"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    condition: Optional[ItemCondition] = Query(None, description="Item condition filter"),
    sort: SortOrder = Query(SortOrder.BEST_MATCH, description="Sort order"),
    category_ids: Optional[str] = Query(None, description="Comma-separated category IDs"),
    buy_it_now_only: bool = Query(False, description="Show only Buy It Now items"),
    free_shipping_only: bool = Query(False, description="Show only items with free shipping"),
    marketplace: str = Query("EBAY_US", description="eBay marketplace"),
    top_rated_sellers_only: bool = Query(False, description="Show only top-rated sellers"),
    min_seller_feedback: Optional[int] = Query(None, ge=0, description="Minimum seller feedback score"),
    max_seller_feedback: Optional[int] = Query(None, ge=0, description="Maximum seller feedback score"),
    item_location_country: Optional[str] = Query(None, description="Item location country (e.g., US, GB, DE)"),
    search_mode: str = Query("enhanced", description="Search mode - 'enhanced', 'exact', 'broad'")
) -> Dict[str, Any]:
    """
    Clean and simple eBay product search with essential filtering options.
    """
    try:
        logger.info(
            f"Search triggered with Keyword: '{keyword}', Limit: {limit}, "
            f"Feedback Range: {min_seller_feedback}-{max_seller_feedback}"
        )
        
        # Process keywords based on search mode
        if search_mode == "exact":
            processed_keyword = f'"{keyword}"'
        elif search_mode == "broad":
            processed_keyword = keyword
        else:  # enhanced mode
            processed_keyword = prepare_search_keywords(keyword)
        
        # Build eBay API compatible filters
        filters = []
        
        # Price filters - Format properly for eBay API
        if min_price is not None and max_price is not None:
            filters.append(f"price:[{min_price}..{max_price}]")
        elif min_price is not None:
            filters.append(f"price:[{min_price}..]")
        elif max_price is not None:
            filters.append(f"price:[..{max_price}]")
        
        # Double-check price filter in results
        def is_price_in_range(item_price: float) -> bool:
            if min_price is not None and item_price < min_price:
                return False
            if max_price is not None and item_price > max_price:
                return False
            return True
        
        # Condition filter
        if condition:
            filters.append(f"conditionIds:{{{condition.value}}}")
        
        # Delivery options
        if free_shipping_only:
            filters.append("deliveryOptions:{FreeShipping}")
        
        # Buying options
        if buy_it_now_only:
            filters.append("buyingOptions:{FIXED_PRICE}")
        
        # Seller filters (only those supported by API)
        if top_rated_sellers_only:
            filters.append("sellerTypes:{TopRated}")
            
        # Location filter
        if item_location_country:
            filters.append(f"itemLocationCountry:{item_location_country}")
        
        # Parse category IDs
        category_list = None
        if category_ids:
            category_list = [cat.strip() for cat in category_ids.split(",")]

        # Always fetch a larger pool of items to allow for shuffling and variety.
        user_requested_limit = limit
        api_limit = 200  # Max limit for eBay Browse API
        logger.info(f"API limit set to {api_limit} to provide varied results.")

        # Call eBay Browse API
        params = {
            "q": processed_keyword,
            "limit": api_limit,
            "sort": sort.value,
            "fieldgroups": "MATCHING_ITEMS,EXTENDED"
        }
        
        # Add filters if any
        if filters:
            params["filter"] = ",".join(filters)
        
        # Add category IDs
        if category_list:
            params["category_ids"] = ",".join(category_list)
        
        # Set marketplace headers
        headers = {
            "X-EBAY-C-MARKETPLACE-ID": marketplace,
            "X-EBAY-C-ENDUSERCTX": f"contextualLocation=country={marketplace.split('_')[1]}"
        }
        
        logger.info(f"Calling eBay API with params: {params}")
        results = await ebay_client.call_api(
            method='GET',
            endpoint='/buy/browse/v1/item_summary/search',
            params=params,
            headers=headers
        )

        # If the API call fails or returns nothing, exit gracefully.
        if not results:
            logger.warning("eBay API returned no results. Returning empty list.")
            return {
                "success": True,
                "results": [],
                "total_found": 0,
                "search_metadata": {"message": "No results from eBay API."}
            }
        
        # Process the results
        processed_results = process_ebay_results(results, marketplace)
        logger.info(f"Received {len(processed_results.get('items', []))} items from eBay.")
        
        # Apply post-search filters (for criteria not supported by eBay's API filter)
        final_items = []
        for item in processed_results.get("items", []):
            # Price range check (as a safeguard)
            try:
                price_value = float(item.get("price", {}).get("value", 0))
                if not is_price_in_range(price_value):
                    continue
            except (ValueError, TypeError):
                continue

            # Seller feedback score filter
            if min_seller_feedback is not None or max_seller_feedback is not None:
                try:
                    seller_feedback = int(item.get("seller", {}).get("feedback_score", 0))
                    if min_seller_feedback is not None and seller_feedback < min_seller_feedback:
                        continue
                    if max_seller_feedback is not None and seller_feedback > max_seller_feedback:
                        continue
                except (ValueError, TypeError):
                    # If feedback score is invalid, it cannot match the filter
                    continue
            
            final_items.append(item)
        
        logger.info(f"Found {len(final_items)} items after applying all filters.")

        # --- NEW: Shuffle results for variety ---
        random.shuffle(final_items)
        logger.info("Shuffled results to provide variety on each search.")

        # Truncate results to the user's originally requested limit
        if len(final_items) > user_requested_limit:
            final_items = final_items[:user_requested_limit]
            logger.info(f"Truncating results to user's limit of {user_requested_limit}.")

        # Create search metadata
        search_metadata = {
            "keyword": keyword,
            "processed_keyword": processed_keyword,
            "search_mode": search_mode,
            "marketplace": marketplace,
            "filters_applied": {
                "price_range": {"min": min_price, "max": max_price},
                "condition": condition.value if condition else None,
                "free_shipping_only": free_shipping_only,
                "buy_it_now_only": buy_it_now_only,
                "top_rated_sellers_only": top_rated_sellers_only,
                "seller_feedback_range": {
                    "min": min_seller_feedback,
                    "max": max_seller_feedback
                },
                "item_location_country": item_location_country,
                "results_limit": limit
            },
            "sort_order": sort.value,
            "results_count": len(final_items),
            "total_available": results.get("total", 0)
        }
        
        # Return clean results
        return {
            "success": True,
            "results": final_items,
            "total_found": len(final_items),
            "search_metadata": search_metadata
        }
        
    except EbayAPIError as e:
        logger.error(f"Caught EbayAPIError in search_products: {e.message}")
        raise HTTPException(
            status_code=e.status_code or 500,
            detail={"error": "eBay API Error", "message": e.message}
        )
    except Exception as e:
        logger.error(f"Unexpected error in search_products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

def process_ebay_results(ebay_response: Dict[str, Any], marketplace: str) -> Dict[str, Any]:
    """
    Process eBay API response and extract essential product information.
    """
    items = []
    
    for item in ebay_response.get("itemSummaries", []):
        item_id = item.get("itemId")
        
        # Extract seller information
        seller_info = item.get("seller", {})
        seller = {
            "username": seller_info.get("username"),
            "feedback_score": int(seller_info.get("feedbackScore", 0)),  # Ensure integer
            "feedback_percentage": seller_info.get("feedbackPercentage"),
            "top_rated_seller": seller_info.get("topRatedSeller", False),
            "business_seller": seller_info.get("sellerAccountType") == "BUSINESS"
        }
        
        # Extract clean, essential data
        processed_item = {
            "item_id": item_id,
            "title": item.get("title"),
            "price": item.get("price", {}),
            "condition": item.get("condition"),
            "condition_id": item.get("conditionId"),
            
            # Item links
            "item_web_url": item.get("itemWebUrl"),
            "view_item_url": item.get("itemWebUrl"),
            
            # Images
            "image_url": item.get("image", {}).get("imageUrl"),
            "thumbnail_images": item.get("thumbnailImages", []),
            
            # Category info
            "categories": item.get("categories", []),
            "primary_category": item.get("categories", [{}])[0] if item.get("categories") else {},
            
            # Shipping info
            "shipping_options": item.get("shippingOptions", []),
            "free_shipping": any(
                option.get("shippingCost", {}).get("value") == "0.0" 
                for option in item.get("shippingOptions", [])
            ),
            
            # Seller information
            "seller": seller,
            
            # Listing details
            "buying_options": item.get("buyingOptions", []),
            "listing_type": determine_listing_type(item.get("buyingOptions", [])),
            
            # Additional metadata
            "returns_accepted": item.get("returnsAccepted", False),
            "top_rated_buying_experience": item.get("topRatedBuyingExperience", False),
            "item_location": item.get("itemLocation", {}),
            "listing_end_date": item.get("listingEndDate"),
            
            # Simple market insights
            "market_insights": extract_basic_market_insights(item)
        }
        
        items.append(processed_item)
    
    return {
        "items": items,
        "total_found": len(items),
        "marketplace": marketplace
    }

def determine_listing_type(buying_options: List[str]) -> str:
    """Determine listing type from buying options."""
    if "AUCTION" in buying_options:
        return "AUCTION"
    elif "FIXED_PRICE" in buying_options or "BUY_IT_NOW" in buying_options:
        return "BUY_IT_NOW"
    else:
        return "UNKNOWN"

def extract_basic_market_insights(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extract basic market insights from eBay data."""
    insights = {}
    
    # Price analysis
    price_info = item.get("price", {})
    if price_info:
        insights["price_value"] = price_info.get("value")
        insights["price_currency"] = price_info.get("currency")
    
    # Basic listing quality indicators
    insights["listing_quality"] = {
        "top_rated_buying_experience": item.get("topRatedBuyingExperience", False),
        "priority_listing": item.get("priorityListing", False),
        "has_multiple_images": len(item.get("thumbnailImages", [])) > 1,
        "shipping_options_count": len(item.get("shippingOptions", [])),
        "returns_accepted": item.get("returnsAccepted", False)
    }
    
    # Basic market positioning
    insights["market_position"] = {
        "listing_type": determine_listing_type(item.get("buyingOptions", [])),
        "has_free_shipping": any(
            option.get("shippingCost", {}).get("value") == "0.0" 
            for option in item.get("shippingOptions", [])
        ),
        "has_coupons": item.get("availableCoupons", False)
    }
    
    return insights

@router.get("/categories")
async def get_popular_categories() -> Dict[str, Any]:
    """Get popular eBay categories for filtering."""
    return {
        "popular_categories": {
            "Electronics": {
                "category_id": "58058",
                "subcategories": {
                    "Cell Phones & Accessories": "15032",
                    "Computers & Tablets": "58058", 
                    "Consumer Electronics": "293",
                    "Video Games": "1249"
                }
            },
            "Fashion": {
                "category_id": "11450",
                "subcategories": {
                    "Men's Clothing": "1059",
                    "Women's Clothing": "15724",
                    "Shoes": "93427",
                    "Jewelry": "281"
                }
            },
            "Home & Garden": {
                "category_id": "11700",
                "subcategories": {
                    "Home Décor": "20081",
                    "Kitchen & Dining": "20625",
                    "Tools & Hardware": "631",
                    "Garden & Patio": "159912"
                }
            },
            "Sports & Outdoors": {
                "category_id": "888",
                "subcategories": {
                    "Fitness Equipment": "15273",
                    "Outdoor Sports": "159043",
                    "Team Sports": "64482"
                }
            },
            "Automotive": {
                "category_id": "6000",
                "subcategories": {
                    "Parts & Accessories": "6030",
                    "Motorcycles": "6024",
                    "Boats": "26429"
                }
            }
        },
        "note": "Use these category IDs in the category_ids parameter to filter search results."
    }