import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from enum import Enum

# Import the API client
from app.ebay_api_client import ebay_client, EbayAPIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])

class SortOrder(str, Enum):
    """Available sort orders for eBay search."""
    PRICE_LOW_TO_HIGH = "price"
    PRICE_HIGH_TO_LOW = "-price"
    ENDING_SOONEST = "endingSoonest"
    NEWLY_LISTED = "newlyListed"
    BEST_MATCH = "bestMatch"
    DISTANCE_NEAREST = "distance"
    WATCH_COUNT = "watchCount"

class ItemCondition(str, Enum):
    """Available item conditions."""
    NEW = "NEW"
    USED = "USED"
    CERTIFIED_REFURBISHED = "CERTIFIED_REFURBISHED"
    EXCELLENT_REFURBISHED = "EXCELLENT_REFURBISHED"
    VERY_GOOD_REFURBISHED = "VERY_GOOD_REFURBISHED"
    GOOD_REFURBISHED = "GOOD_REFURBISHED"
    SELLER_REFURBISHED = "SELLER_REFURBISHED"
    FOR_PARTS_OR_NOT_WORKING = "FOR_PARTS_OR_NOT_WORKING"

@router.get("/search")
async def search_products(
    keyword: str = Query(..., min_length=1, max_length=100, description="Search keyword"),
    limit: int = Query(20, ge=1, le=200, description="Number of results to return"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    condition: Optional[ItemCondition] = Query(None, description="Item condition filter"),
    sort: SortOrder = Query(SortOrder.BEST_MATCH, description="Sort order"),
    category_ids: Optional[str] = Query(None, description="Comma-separated category IDs"),
    buy_it_now_only: bool = Query(False, description="Show only Buy It Now items"),
    free_shipping_only: bool = Query(False, description="Show only items with free shipping"),
    sold_items_only: bool = Query(False, description="Show only sold items (for research)"),
    min_sold_count: Optional[int] = Query(None, ge=0, description="Minimum sold count filter"),
    marketplace: str = Query("EBAY_US", description="eBay marketplace")
) -> Dict[str, Any]:
    """
    Advanced eBay product search with filtering, item links, and sold counts.
    """
    try:
        # Build filters
        filters = {}
        
        # Price filters
        if min_price is not None and max_price is not None:
            filters["price"] = f"[{min_price}..{max_price}]"
        elif min_price is not None:
            filters["price"] = f"[{min_price}..]"
        elif max_price is not None:
            filters["price"] = f"[..{max_price}]"
        
        # Condition filter
        if condition:
            filters["condition"] = condition.value
        
        # Buy It Now only
        if buy_it_now_only:
            filters["buyingOptions"] = "FIXED_PRICE"
        
        # Free shipping only
        if free_shipping_only:
            filters["deliveryOptions"] = "FREE_SHIPPING"
        
        # Sold items only (for market research)
        if sold_items_only:
            filters["soldItems"] = "true"
        
        # Parse category IDs
        category_list = None
        if category_ids:
            category_list = [cat.strip() for cat in category_ids.split(",")]
        
        # Use the ebay_client to search for products
        results = await ebay_client.search_products(
            keyword=keyword,
            limit=limit,
            category_ids=category_list,
            filters=filters,
            sort=sort.value,
            marketplace_id=marketplace
        )
        
        # Enhance the results with additional data
        enhanced_results = await enhance_search_results(
            results.get("itemSummaries", []),
            min_sold_count=min_sold_count,
            marketplace=marketplace
        )
        
        # Return enhanced results
        return {
            "success": True,
            "results": enhanced_results,
            "total_found": results.get("total", 0),
            "search_metadata": {
                "keyword": keyword,
                "marketplace": marketplace,
                "filters_applied": filters,
                "sort_order": sort.value,
                "results_count": len(enhanced_results),
                "total_available": results.get("total", 0)
            }
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

async def enhance_search_results(
    items: List[Dict[str, Any]], 
    min_sold_count: Optional[int] = None,
    marketplace: str = "EBAY_US"
) -> List[Dict[str, Any]]:
    """
    Enhance search results with additional data like item links and sold counts.
    """
    enhanced_items = []
    
    for item in items:
        # Extract and enhance item data
        enhanced_item = {
            "item_id": item.get("itemId"),
            "title": item.get("title"),
            "price": item.get("price", {}),
            "condition": item.get("condition"),
            "category": item.get("categories", [{}])[0] if item.get("categories") else {},
            "image_url": item.get("image", {}).get("imageUrl"),
            "thumbnail_images": item.get("thumbnailImages", []),
            
            # Item links
            "item_web_url": item.get("itemWebUrl"),
            "item_affiliate_web_url": item.get("itemAffiliateWebUrl"),
            "view_item_url": item.get("viewItemURL"),
            
            # Shipping info
            "shipping_options": item.get("shippingOptions", []),
            "shipping_cost": item.get("shippingCost"),
            "free_shipping": any(
                option.get("shippingCost", {}).get("value") == "0.0" 
                for option in item.get("shippingOptions", [])
            ),
            
            # Seller info
            "seller": item.get("seller", {}),
            "seller_feedback_percentage": item.get("seller", {}).get("feedbackPercentage"),
            "seller_feedback_score": item.get("seller", {}).get("feedbackScore"),
            
            # Additional details
            "buying_options": item.get("buyingOptions", []),
            "bid_count": item.get("bidCount"),
            "current_bid_price": item.get("currentBidPrice"),
            "distance": item.get("distance"),
            "item_location": item.get("itemLocation"),
            "listing_marketplace_id": item.get("listingMarketplaceId"),
            
            # Sold count estimation (if available)
            "quantity_sold": item.get("quantitySold"),
            "watch_count": item.get("watchCount"),
            
            # Market insights
            "market_insights": extract_market_insights(item),
            
            # Listing details
            "listing_type": determine_listing_type(item),
            "time_left": item.get("timeLeft"),
            "listing_end_time": item.get("itemEndDate"),
            
            # Additional metadata
            "last_updated": item.get("lastUpdated"),
            "item_creation_date": item.get("itemCreationDate"),
            "pickup_options": item.get("pickupOptions", []),
            "return_policy": item.get("returnPolicy", {}),
            "top_rated_listing": item.get("topRatedListing", False),
            "priority_listing": item.get("priorityListing", False),
            "fast_and_free": item.get("fastAndFree", False)
        }
        
        # Apply sold count filter if specified
        if min_sold_count is not None:
            quantity_sold = enhanced_item.get("quantity_sold", 0)
            if isinstance(quantity_sold, (int, float)) and quantity_sold >= min_sold_count:
                enhanced_items.append(enhanced_item)
            elif quantity_sold is None:
                # Include items where sold count is unknown
                enhanced_items.append(enhanced_item)
        else:
            enhanced_items.append(enhanced_item)
    
    return enhanced_items

def extract_market_insights(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extract market insights from item data."""
    insights = {}
    
    # Price analysis
    price_info = item.get("price", {})
    if price_info:
        insights["price_value"] = price_info.get("value")
        insights["price_currency"] = price_info.get("currency")
        insights["price_converted"] = price_info.get("convertedFromValue")
    
    # Demand indicators
    insights["watch_count"] = item.get("watchCount")
    insights["bid_count"] = item.get("bidCount")
    
    # Seller performance
    seller = item.get("seller", {})
    if seller:
        insights["seller_reputation"] = {
            "feedback_percentage": seller.get("feedbackPercentage"),
            "feedback_score": seller.get("feedbackScore"),
            "top_rated_seller": seller.get("topRatedSeller", False)
        }
    
    # Listing quality indicators
    insights["listing_quality"] = {
        "top_rated_listing": item.get("topRatedListing", False),
        "priority_listing": item.get("priorityListing", False),
        "fast_and_free": item.get("fastAndFree", False),
        "has_multiple_images": len(item.get("thumbnailImages", [])) > 1
    }
    
    return insights

def determine_listing_type(item: Dict[str, Any]) -> str:
    """Determine the type of listing (auction, buy-it-now, etc.)."""
    buying_options = item.get("buyingOptions", [])
    
    if "FIXED_PRICE" in buying_options and "AUCTION" in buying_options:
        return "AUCTION_WITH_BUY_IT_NOW"
    elif "FIXED_PRICE" in buying_options:
        return "BUY_IT_NOW"
    elif "AUCTION" in buying_options:
        return "AUCTION"
    else:
        return "UNKNOWN"

@router.get("/search/advanced")
async def advanced_search(
    keyword: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=200),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    condition: Optional[ItemCondition] = Query(None),
    sort: SortOrder = Query(SortOrder.BEST_MATCH),
    category_ids: Optional[str] = Query(None),
    buy_it_now_only: bool = Query(False),
    free_shipping_only: bool = Query(False),
    sold_items_only: bool = Query(False),
    min_sold_count: Optional[int] = Query(None, ge=0),
    marketplace: str = Query("EBAY_US"),
    # Additional advanced filters
    min_feedback_score: Optional[int] = Query(None, ge=0, description="Minimum seller feedback score"),
    min_feedback_percentage: Optional[float] = Query(None, ge=0, le=100, description="Minimum seller feedback percentage"),
    top_rated_sellers_only: bool = Query(False, description="Show only top-rated sellers"),
    auction_only: bool = Query(False, description="Show only auction items"),
    exclude_categories: Optional[str] = Query(None, description="Comma-separated category IDs to exclude"),
    search_in_description: bool = Query(False, description="Search in item descriptions too"),
    max_distance: Optional[int] = Query(None, ge=0, description="Maximum distance from location (miles)"),
    location_zip: Optional[str] = Query(None, description="ZIP code for location-based search")
) -> Dict[str, Any]:
    """
    Advanced search with comprehensive filtering options.
    """
    # This endpoint provides additional filtering on top of the basic search
    # Call the basic search first, then apply additional filters
    results = await search_products(
        keyword=keyword,
        limit=limit,
        min_price=min_price,
        max_price=max_price,
        condition=condition,
        sort=sort,
        category_ids=category_ids,
        buy_it_now_only=buy_it_now_only,
        free_shipping_only=free_shipping_only,
        sold_items_only=sold_items_only,
        min_sold_count=min_sold_count,
        marketplace=marketplace
    )
    
    # Apply additional filters
    filtered_results = apply_advanced_filters(
        results["results"],
        min_feedback_score=min_feedback_score,
        min_feedback_percentage=min_feedback_percentage,
        top_rated_sellers_only=top_rated_sellers_only,
        auction_only=auction_only,
        exclude_categories=exclude_categories,
        max_distance=max_distance
    )
    
    results["results"] = filtered_results
    results["search_metadata"]["advanced_filters_applied"] = True
    results["search_metadata"]["results_after_advanced_filtering"] = len(filtered_results)
    
    return results

def apply_advanced_filters(
    items: List[Dict[str, Any]],
    min_feedback_score: Optional[int] = None,
    min_feedback_percentage: Optional[float] = None,
    top_rated_sellers_only: bool = False,
    auction_only: bool = False,
    exclude_categories: Optional[str] = None,
    max_distance: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Apply advanced filtering to search results."""
    filtered_items = []
    
    # Parse excluded categories
    excluded_cats = []
    if exclude_categories:
        excluded_cats = [cat.strip() for cat in exclude_categories.split(",")]
    
    for item in items:
        # Apply filters
        if min_feedback_score is not None:
            seller_score = item.get("seller_feedback_score", 0)
            if seller_score < min_feedback_score:
                continue
        
        if min_feedback_percentage is not None:
            seller_percentage = item.get("seller_feedback_percentage", 0)
            if seller_percentage < min_feedback_percentage:
                continue
        
        if top_rated_sellers_only:
            seller_info = item.get("seller", {})
            if not seller_info.get("topRatedSeller", False):
                continue
        
        if auction_only:
            if item.get("listing_type") != "AUCTION":
                continue
        
        if excluded_cats:
            item_category = item.get("category", {}).get("categoryId")
            if item_category in excluded_cats:
                continue
        
        if max_distance is not None:
            distance = item.get("distance", {})
            if distance and distance.get("value", float('inf')) > max_distance:
                continue
        
        filtered_items.append(item)
    
    return filtered_items

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
        }
    }

@router.get("/item/{item_id}/details")
async def get_item_details(
    item_id: str,
    marketplace: str = Query("EBAY_US", description="eBay marketplace")
) -> Dict[str, Any]:
    """
    Get detailed information for a specific item including sold count history.
    """
    try:
        # Get detailed item information
        details = await ebay_client.get_item_details(
            item_ids=[item_id],
            fieldgroups=["PRODUCT", "EXTENDED"],
            marketplace_id=marketplace
        )
        
        if not details.get("items"):
            raise HTTPException(status_code=404, detail="Item not found")
        
        item = details["items"][0]
        
        # Enhance with additional details
        enhanced_details = {
            "item_id": item.get("itemId"),
            "title": item.get("title"),
            "price": item.get("price"),
            "condition": item.get("condition"),
            "category": item.get("categories", [{}])[0] if item.get("categories") else {},
            "description": item.get("description"),
            "product_details": item.get("product", {}),
            "images": item.get("images", []),
            "seller_details": item.get("seller", {}),
            "shipping_options": item.get("shippingOptions", []),
            "return_policy": item.get("returnPolicy", {}),
            "estimated_availabilities": item.get("estimatedAvailabilities", []),
            "item_web_url": item.get("itemWebUrl"),
            "quantity_sold": item.get("quantitySold"),
            "watch_count": item.get("watchCount"),
            "bid_count": item.get("bidCount"),
            "listing_marketplace_id": item.get("listingMarketplaceId"),
            "primary_item_group": item.get("primaryItemGroup", {}),
            "additional_images": item.get("additionalImages", []),
            "aspect_groups": item.get("aspectGroups", []),
            "authentic_guarantee": item.get("authenticGuarantee", {}),
            "available_coupons": item.get("availableCoupons", []),
            "eco_participation_fee": item.get("ecoParticipationFee", {}),
            "item_location": item.get("itemLocation"),
            "lot_size": item.get("lotSize"),
            "marketing_price": item.get("marketingPrice", {}),
            "qualified_programs": item.get("qualifiedPrograms", []),
            "sales_tax": item.get("salesTax", {}),
            "unique_bid_count": item.get("uniqueBidderCount")
        }
        
        return {
            "success": True,
            "item_details": enhanced_details
        }
        
    except EbayAPIError as e:
        logger.error(f"Error getting item details: {e.message}")
        raise HTTPException(
            status_code=e.status_code or 500,
            detail={"error": "eBay API Error", "message": e.message}
        )
    except Exception as e:
        logger.error(f"Unexpected error getting item details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/sold-research")
async def research_sold_items(
    keyword: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(50, ge=1, le=200),
    days_back: int = Query(30, ge=1, le=90, description="Days to look back for sold items"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    condition: Optional[ItemCondition] = Query(None),
    marketplace: str = Query("EBAY_US")
) -> Dict[str, Any]:
    """
    Research sold items for market analysis and pricing insights.
    """
    # This is a specialized endpoint for dropshipping research
    return await search_products(
        keyword=keyword,
        limit=limit,
        min_price=min_price,
        max_price=max_price,
        condition=condition,
        sort=SortOrder.ENDING_SOONEST,
        sold_items_only=True,
        marketplace=marketplace
    )