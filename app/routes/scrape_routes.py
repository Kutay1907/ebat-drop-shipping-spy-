"""
Scraping Routes Module
====================

API routes for scraping product data from various e-commerce platforms.
Currently supports Amazon product scraping for eBay listing creation.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl, validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.amazon_scraper import amazon_scraper, AmazonScraperError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scrape", tags=["scraping"])

class AmazonScrapeRequest(BaseModel):
    """Request model for Amazon product scraping."""
    amazon_url: str
    
    @validator('amazon_url')
    def validate_amazon_url(cls, v):
        """Validate that the URL is a valid Amazon product URL."""
        if not v:
            raise ValueError("Amazon URL is required")
        
        # Convert to string if needed and clean
        url_str = str(v).strip()
        
        # Basic Amazon URL validation
        amazon_domains = [
            'amazon.com', 'amazon.co.uk', 'amazon.ca', 'amazon.de',
            'amazon.fr', 'amazon.it', 'amazon.es', 'amazon.co.jp'
        ]
        
        # Check if it's an Amazon URL
        is_amazon = any(domain in url_str.lower() for domain in amazon_domains)
        if not is_amazon:
            raise ValueError("URL must be from Amazon")
        
        # Check for product indicators
        product_indicators = ['/dp/', '/gp/product/', 'ASIN=']
        has_product = any(indicator in url_str for indicator in product_indicators)
        if not has_product:
            raise ValueError("URL must be a valid Amazon product page")
        
        return url_str

class AmazonScrapeResponse(BaseModel):
    """Response model for Amazon product scraping."""
    success: bool
    title: str
    price: Optional[float] = None
    images: list[str] = []
    description: str = ""
    specifics: Dict[str, str] = {}
    message: str = ""
    
    class Config:
        json_encoders = {
            float: lambda v: round(v, 2) if v else None
        }

@router.post("/amazon", response_model=AmazonScrapeResponse)
async def scrape_amazon_product(
    request: AmazonScrapeRequest,
    db: Session = Depends(get_db)
):
    """
    Scrape Amazon product data for eBay listing creation.
    
    This endpoint extracts:
    - Product title (optimized to 80 characters)
    - Product images (cleaned URLs, up to 12 images)
    - Product description (cleaned HTML with bullets)
    - Product price
    - Item specifics (brand, dimensions, etc.)
    
    Args:
        request: Amazon scrape request with product URL
        
    Returns:
        Structured product data ready for eBay listing
    """
    try:
        logger.info(f"Starting Amazon scrape for URL: {request.amazon_url}")
        
        # Scrape the Amazon product
        product_data = await amazon_scraper.scrape_product(request.amazon_url)
        
        # Validate scraped data
        if not product_data.get('title'):
            raise HTTPException(
                status_code=422,
                detail="Could not extract product title from Amazon page"
            )
        
        # Format the response
        response = AmazonScrapeResponse(
            success=True,
            title=product_data['title'],
            price=product_data.get('price'),
            images=product_data.get('images', []),
            description=product_data.get('description', ''),
            specifics=product_data.get('specifics', {}),
            message=f"Successfully scraped Amazon product: {product_data['title'][:50]}..."
        )
        
        logger.info(f"Successfully scraped Amazon product: {response.title}")
        logger.info(f"Extracted {len(response.images)} images, price: ${response.price}")
        
        return response
        
    except AmazonScraperError as e:
        logger.error(f"Amazon scraping error: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to scrape Amazon product: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in Amazon scraping: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while scraping the product"
        )

@router.get("/test")
async def test_scraper():
    """Test endpoint to verify scraper functionality."""
    return {
        "status": "ok",
        "message": "Amazon scraper service is available",
        "endpoints": [
            "POST /api/scrape/amazon - Scrape Amazon product data"
        ]
    } 