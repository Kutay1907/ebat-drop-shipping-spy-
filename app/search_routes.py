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

class ItemCondition(str, Enum):
    """Available item conditions."""
    NEW = "1000"
    USED = "3000"
    CERTIFIED_REFURBISHED = "2000"
    EXCELLENT_REFURBISHED = "2010"
    VERY_GOOD_REFURBISHED = "2020"
    GOOD_REFURBISHED = "2030"
    SELLER_REFURBISHED = "2500"
    FOR_PARTS_OR_NOT_WORKING = "7000"

class DeliveryOptions(str, Enum):
    """Delivery option filters."""
    FREE_SHIPPING = "FreeShipping"
    FAST_N_FREE = "FastAndFree"
    
class BuyingOptions(str, Enum):
    """Buying option filters."""
    FIXED_PRICE = "FIXED_PRICE"
    AUCTION = "AUCTION"
    BEST_OFFER = "BEST_OFFER"

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
    marketplace: str = Query("EBAY_US", description="eBay marketplace"),
    # Additional filters matching eBay's actual API
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
        if min_price is not None and max_price is not None:
            filters.append(f"price:[{min_price}..{max_price}]")
        elif min_price is not None:
            filters.append(f"price:[{min_price}..]")
        elif max_price is not None:
            filters.append(f"price:[..{max_price}]")
        
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
        
        # Parse category IDs
        category_list = None
        if category_ids:
            category_list = [cat.strip() for cat in category_ids.split(",")]
        
        # Parse charity IDs
        charity_list = None
        if charity_ids:
            charity_list = [charity.strip() for charity in charity_ids.split(",")]
        
        # Call eBay API with proper parameters
        params = {
            "q": keyword,
            "limit": limit,
            "sort": sort.value
        }
        
        # Add filters if any
        if filters:
            params["filter"] = ",".join(filters)
        
        # Add category IDs
        if category_list:
            params["category_ids"] = ",".join(category_list)
        
        # Add charity IDs
        if charity_list:
            params["charity_ids"] = ",".join(charity_list)
        
        # Use the ebay_client to search for products
        results = await ebay_client.call_api(
            method='GET',
            endpoint='/buy/browse/v1/item_summary/search',
            params=params
        )
        
        # Process and enhance the results
        enhanced_results = process_ebay_results(results, marketplace)
        
        # Return enhanced results
        return {
            "success": True,
            "results": enhanced_results.get("items", []),
            "total_found": results.get("total", 0),
            "search_metadata": {
                "keyword": keyword,
                "marketplace": marketplace,
                "filters_applied": filters,
                "sort_order": sort.value,
                "results_count": len(enhanced_results.get("items", [])),
                "total_available": results.get("total", 0),
                "ebay_search_url": results.get("href", ""),
                "warnings": results.get("warnings", [])
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

def process_ebay_results(ebay_response: Dict[str, Any], marketplace: str) -> Dict[str, Any]:
    """
    Process eBay API response and extract available data according to actual eBay API fields.
    """
    items = []
    
    for item in ebay_response.get("itemSummaries", []):
        # Extract data that eBay actually provides
        processed_item = {
            "item_id": item.get("itemId"),
            "title": item.get("title"),
            "price": item.get("price", {}),
            "condition": item.get("condition"),
            "condition_id": item.get("conditionId"),
            
            # Item links - eBay provides these fields
            "item_web_url": item.get("itemWebUrl"),
            "item_affiliate_web_url": item.get("itemAffiliateWebUrl"),
            "view_item_url": item.get("itemWebUrl"),  # Same as itemWebUrl
            
            # Images
            "image_url": item.get("image", {}).get("imageUrl"),
            "thumbnail_images": item.get("thumbnailImages", []),
            "additional_images": item.get("additionalImages", []),
            
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
            "seller": item.get("seller", {}),
            "seller_feedback_percentage": item.get("seller", {}).get("feedbackPercentage"),
            "seller_feedback_score": item.get("seller", {}).get("feedbackScore"),
            "seller_username": item.get("seller", {}).get("username"),
            
            # Listing details
            "buying_options": item.get("buyingOptions", []),
            "listing_type": determine_listing_type(item.get("buyingOptions", [])),
            "item_location": item.get("itemLocation", {}),
            "listing_marketplace_id": item.get("listingMarketplaceId"),
            
            # Bidding/Auction data (available for auctions)
            "bid_count": item.get("bidCount", 0),
            "current_bid_price": item.get("currentBidPrice"),
            
            # Watch count (requires special eBay permission)
            "watch_count": item.get("watchCount"),
            
            # Timing information
            "item_creation_date": item.get("itemCreationDate"),
            "item_end_date": item.get("itemEndDate"),
            "time_left": calculate_time_left(item.get("itemEndDate")),
            
            # Listing quality indicators
            "top_rated_buying_experience": item.get("topRatedBuyingExperience", False),
            "priority_listing": item.get("priorityListing", False),
            "qualified_programs": item.get("qualifiedPrograms", []),
            
            # Additional details
            "pickup_options": item.get("pickupOptions", []),
            "distance_from_buyer": item.get("distance"),
            "short_description": item.get("shortDescription"),
            "adult_only": item.get("adultOnly", False),
            "available_coupons": item.get("availableCoupons", False),
            "energy_efficiency_class": item.get("energyEfficiencyClass"),
            "epid": item.get("epid"),  # eBay Product ID
            
            # Market insights based on available data
            "market_insights": extract_market_insights_from_actual_data(item),
            
            # Note about sold count limitations
            "sold_count_note": "Sold count data requires special eBay API permissions and is limited. Watch count and bid count are more readily available indicators of popularity."
        }
        
        items.append(processed_item)
    
    return {
        "items": items,
        "refinements": ebay_response.get("refinement", {}),
        "auto_corrections": ebay_response.get("autoCorrections", {}),
        "warnings": ebay_response.get("warnings", [])
    }

def determine_listing_type(buying_options: List[str]) -> str:
    """Determine the type of listing based on buying options."""
    if not buying_options:
        return "UNKNOWN"
    
    if "FIXED_PRICE" in buying_options and "AUCTION" in buying_options:
        return "AUCTION_WITH_BUY_IT_NOW"
    elif "FIXED_PRICE" in buying_options:
        return "BUY_IT_NOW"
    elif "AUCTION" in buying_options:
        return "AUCTION"
    elif "BEST_OFFER" in buying_options:
        return "BEST_OFFER"
    else:
        return "OTHER"

def calculate_time_left(end_date: Optional[str]) -> Optional[str]:
    """Calculate time left in listing from end date."""
    if not end_date:
        return None
    
    try:
        from datetime import datetime, timezone
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        if end_dt <= now:
            return "ENDED"
        
        time_diff = end_dt - now
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return None

def extract_market_insights_from_actual_data(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extract market insights from available eBay data."""
    insights = {}
    
    # Price analysis
    price_info = item.get("price", {})
    if price_info:
        insights["price_value"] = price_info.get("value")
        insights["price_currency"] = price_info.get("currency")
        insights["converted_price"] = price_info.get("convertedFromValue")
    
    # Popularity indicators (what's actually available)
    insights["popularity_indicators"] = {
        "watch_count": item.get("watchCount"),  # May be None if no permission
        "bid_count": item.get("bidCount", 0),
        "has_bids": item.get("bidCount", 0) > 0,
        "current_bid_price": item.get("currentBidPrice")
    }
    
    # Seller quality indicators
    seller = item.get("seller", {})
    insights["seller_quality"] = {
        "feedback_percentage": seller.get("feedbackPercentage"),
        "feedback_score": seller.get("feedbackScore"),
        "username": seller.get("username")
    }
    
    # Listing quality indicators
    insights["listing_quality"] = {
        "top_rated_buying_experience": item.get("topRatedBuyingExperience", False),
        "priority_listing": item.get("priorityListing", False),
        "qualified_programs": item.get("qualifiedPrograms", []),
        "has_multiple_images": len(item.get("thumbnailImages", [])) > 1,
        "shipping_options_count": len(item.get("shippingOptions", []))
    }
    
    # Market positioning
    insights["market_position"] = {
        "listing_type": determine_listing_type(item.get("buyingOptions", [])),
        "has_free_shipping": any(
            option.get("shippingCost", {}).get("value") == "0.0" 
            for option in item.get("shippingOptions", [])
        ),
        "has_coupons": item.get("availableCoupons", False),
        "adult_only": item.get("adultOnly", False)
    }
    
    return insights

@router.get("/item/{item_id}")
async def get_item_details(
    item_id: str,
    marketplace: str = Query("EBAY_US", description="eBay marketplace")
) -> Dict[str, Any]:
    """
    Get detailed information for a specific item.
    This endpoint provides more detailed data including estimated availability.
    """
    try:
        # Get detailed item information using eBay's getItem endpoint
        result = await ebay_client.call_api(
            method='GET',
            endpoint=f'/buy/browse/v1/item/{item_id}',
            params={}
        )
        
        # Process the detailed item data
        detailed_item = {
            "item_id": result.get("itemId"),
            "title": result.get("title"),
            "description": result.get("description"),
            "price": result.get("price"),
            "condition": result.get("condition"),
            "condition_id": result.get("conditionId"),
            "condition_description": result.get("conditionDescription"),
            
            # Direct eBay links
            "item_web_url": result.get("itemWebUrl"),
            "item_affiliate_web_url": result.get("itemAffiliateWebUrl"),
            
            # Detailed images
            "primary_image": result.get("image"),
            "additional_images": result.get("additionalImages", []),
            
            # Seller details
            "seller": result.get("seller", {}),
            
            # Availability information (this is where we get closest to "sold count")
            "estimated_availabilities": result.get("estimatedAvailabilities", []),
            
            # Watch count (if available)
            "watch_count": result.get("watchCount"),
            
            # Bidding information
            "bid_count": result.get("bidCount"),
            "unique_bidder_count": result.get("uniqueBidderCount"),
            "current_bid_price": result.get("currentBidPrice"),
            "minimum_price_to_bid": result.get("minimumPriceToBid"),
            
            # Shipping and policies
            "shipping_options": result.get("shippingOptions", []),
            "return_terms": result.get("returnTerms", {}),
            
            # Additional metadata
            "item_creation_date": result.get("itemCreationDate"),
            "item_end_date": result.get("itemEndDate"),
            "listing_marketplace_id": result.get("listingMarketplaceId"),
            "qualified_programs": result.get("qualifiedPrograms", []),
            "top_rated_buying_experience": result.get("topRatedBuyingExperience", False)
        }
        
        return {
            "success": True,
            "item_details": detailed_item,
            "availability_note": "eBay provides estimated availability data instead of exact sold counts. Watch count and bid data require special permissions."
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

@router.get("/research/market-analysis")
async def market_analysis(
    keyword: str = Query(..., description="Product keyword to analyze"),
    category_id: Optional[str] = Query(None, description="Category to focus analysis on"),
    limit: int = Query(100, ge=10, le=200, description="Number of items to analyze")
) -> Dict[str, Any]:
    """
    Perform market analysis using available eBay data.
    This provides insights for dropshipping research using publicly available data.
    """
    try:
        # Get both active and completed listings for analysis
        active_results = await ebay_client.call_api(
            method='GET',
            endpoint='/buy/browse/v1/item_summary/search',
            params={
                "q": keyword,
                "limit": limit,
                "category_ids": category_id if category_id else "",
                "sort": "newlyListed"
            }
        )
        
        # Analyze the data
        analysis = analyze_market_data(active_results, keyword)
        
        return {
            "success": True,
            "keyword": keyword,
            "category_id": category_id,
            "analysis": analysis,
            "disclaimer": "This analysis is based on publicly available eBay data. For comprehensive sold item analysis, eBay Terapeak or similar premium tools are recommended."
        }
        
    except Exception as e:
        logger.error(f"Error in market analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Market analysis failed: {str(e)}")

def analyze_market_data(ebay_data: Dict[str, Any], keyword: str) -> Dict[str, Any]:
    """Analyze market data from eBay search results."""
    items = ebay_data.get("itemSummaries", [])
    
    if not items:
        return {"error": "No items found for analysis"}
    
    # Price analysis
    prices = []
    for item in items:
        price_info = item.get("price", {})
        if price_info and price_info.get("value"):
            try:
                prices.append(float(price_info["value"]))
            except (ValueError, TypeError):
                continue
    
    # Competition analysis
    seller_count = len(set(item.get("seller", {}).get("username", "") for item in items))
    
    # Listing type distribution
    listing_types = {}
    for item in items:
        buying_options = item.get("buyingOptions", [])
        listing_type = determine_listing_type(buying_options)
        listing_types[listing_type] = listing_types.get(listing_type, 0) + 1
    
    # Popular categories
    categories = {}
    for item in items:
        for category in item.get("categories", []):
            cat_name = category.get("categoryName", "Unknown")
            categories[cat_name] = categories.get(cat_name, 0) + 1
    
    analysis = {
        "total_listings": len(items),
        "unique_sellers": seller_count,
        "price_analysis": {
            "average_price": sum(prices) / len(prices) if prices else 0,
            "min_price": min(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
            "price_range": max(prices) - min(prices) if prices else 0,
            "total_analyzed": len(prices)
        },
        "listing_type_distribution": listing_types,
        "popular_categories": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]),
        "market_insights": {
            "competition_level": "High" if seller_count > 50 else "Medium" if seller_count > 20 else "Low",
            "price_variation": "High" if (max(prices) - min(prices) if prices else 0) > 100 else "Medium" if (max(prices) - min(prices) if prices else 0) > 20 else "Low",
            "dominant_listing_type": max(listing_types.items(), key=lambda x: x[1])[0] if listing_types else "Unknown"
        },
        "recommendations": generate_market_recommendations(len(items), seller_count, prices, listing_types)
    }
    
    return analysis

def generate_market_recommendations(total_items: int, seller_count: int, prices: List[float], listing_types: Dict[str, int]) -> List[str]:
    """Generate market recommendations based on analysis."""
    recommendations = []
    
    if total_items > 100:
        recommendations.append("High market saturation - consider niche variations or unique selling propositions")
    elif total_items < 20:
        recommendations.append("Low competition market - potential opportunity for new entrants")
    
    if seller_count < total_items * 0.3:
        recommendations.append("Market dominated by few sellers - analyze top sellers' strategies")
    
    if prices:
        price_range = max(prices) - min(prices)
        if price_range > 100:
            recommendations.append("Wide price range suggests market segmentation opportunities")
        elif price_range < 10:
            recommendations.append("Narrow price range indicates competitive pricing pressure")
    
    if listing_types.get("AUCTION", 0) > listing_types.get("BUY_IT_NOW", 0):
        recommendations.append("Auction format popular - consider timed listings for better visibility")
    
    return recommendations