from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any

# Import the API client
from app.ebay_api_client import ebay_client, EbayAPIError

router = APIRouter(prefix="/api", tags=["search"])

@router.get("/search")
async def search_products(
    keyword: str = Query(..., min_length=1, max_length=100, description="Search keyword"),
    limit: int = Query(20, ge=1, le=200, description="Number of results to return")
) -> Dict[str, Any]:
    """
    Search eBay products using a keyword.
    """
    try:
        # Use the ebay_client to search for products
        results = await ebay_client.search_products(
            keyword=keyword,
            limit=limit
        )
        
        # Return the items found
        return {
            "success": True,
            "results": results.get("itemSummaries", []),
            "total_found": results.get("total", 0)
        }
    except EbayAPIError as e:
        # If the eBay API returns an error, pass it on
        raise HTTPException(
            status_code=e.status_code or 500,
            detail={"error": "eBay API Error", "message": e.message}
        )
    except Exception as e:
        # For any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")