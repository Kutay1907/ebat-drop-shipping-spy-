"""
Domain Models

Core business entities and value objects for the eBay scraper.
These models define the structure of our business data.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl


class ScrapingStatus(str, Enum):
    """Status enumeration for scraping operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


class ProductCondition(str, Enum):
    """eBay product condition enumeration."""
    ANY = "any"
    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"
    FOR_PARTS = "for_parts"
    UNKNOWN = "unknown"


class Marketplace(str, Enum):
    """Supported eBay marketplaces."""
    EBAY_US = "ebay.com"
    EBAY_UK = "ebay.co.uk"
    EBAY_DE = "ebay.de"
    EBAY_FR = "ebay.fr"
    EBAY_IT = "ebay.it"
    EBAY_ES = "ebay.es"
    EBAY_CA = "ebay.ca"
    EBAY_AU = "ebay.com.au"


class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    XLSX = "xlsx"
    HTML = "html"
    JSON = "json"


class CaptchaStatus(str, Enum):
    """CAPTCHA handling status."""
    NOT_DETECTED = "not_detected"
    DETECTED = "detected"
    WAITING_MANUAL_SOLVE = "waiting_manual_solve"
    SOLVED = "solved"
    FAILED = "failed"


class UserAgentHealth(str, Enum):
    """User agent health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    TAINTED = "tainted"
    BLOCKED = "blocked"


class PriceRange(BaseModel):
    """Value object representing a price range."""
    min_price: Decimal = Field(..., ge=0, description="Minimum price")
    max_price: Decimal = Field(..., ge=0, description="Maximum price")
    currency: str = Field(default="USD", description="Currency code")

    @validator('max_price')
    def max_greater_than_min(cls, v, values):
        """Ensure max price is greater than or equal to min price."""
        if 'min_price' in values and v < values['min_price']:
            raise ValueError('max_price must be >= min_price')
        return v


class SellerInfo(BaseModel):
    """Information about a seller."""
    seller_name: str = Field(..., description="Seller username")
    feedback_score: Optional[int] = Field(None, description="Seller feedback score")
    feedback_percentage: Optional[float] = Field(None, ge=0, le=100, description="Positive feedback %")
    location: Optional[str] = Field(None, description="Seller location")
    total_sold_items: Optional[int] = Field(None, ge=0, description="Total items sold by seller")


class Product(BaseModel):
    """Core product entity representing an eBay item."""
    item_id: str = Field(..., description="eBay item ID")
    title: str = Field(..., min_length=1, max_length=500, description="Product title")
    price: Decimal = Field(..., ge=0, description="Current price")
    condition: ProductCondition = Field(default=ProductCondition.UNKNOWN)
    sold_count: Optional[int] = Field(None, ge=0, description="Number of items sold")
    item_url: HttpUrl = Field(..., description="eBay item URL")
    image_url: Optional[HttpUrl] = Field(None, description="Product image URL")
    seller_info: Optional[SellerInfo] = Field(None, description="Seller information")
    shipping_cost: Optional[Decimal] = Field(None, ge=0, description="Shipping cost")
    free_shipping: bool = Field(default=False, description="Whether shipping is free")
    location: Optional[str] = Field(None, description="Item location")
    listing_date: Optional[datetime] = Field(None, description="When item was listed")
    end_date: Optional[datetime] = Field(None, description="Auction end date")
    marketplace: Marketplace = Field(default=Marketplace.EBAY_US, description="Source marketplace")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class TrendPoint(BaseModel):
    """Data point for market trend analysis."""
    date: datetime = Field(..., description="Date of the data point")
    avg_price: Decimal = Field(..., ge=0, description="Average price on this date")
    sales_volume: int = Field(..., ge=0, description="Number of sales")
    active_listings: int = Field(..., ge=0, description="Number of active listings")


class MarketAnalysis(BaseModel):
    """Market analysis results from Terapeak or calculated data."""
    keyword: str = Field(..., min_length=1, description="Search keyword")
    avg_sold_price: Decimal = Field(..., ge=0, description="Average sold price")
    price_range: PriceRange = Field(..., description="Price range")
    sell_through_rate: float = Field(..., ge=0, le=100, description="Sell-through percentage")
    free_shipping_rate: float = Field(..., ge=0, le=100, description="Free shipping percentage")
    seller_count: int = Field(..., ge=0, description="Number of unique sellers")
    total_sales: int = Field(..., ge=0, description="Total sales in period")
    trend_data: List[TrendPoint] = Field(default_factory=list, description="30-day trend data")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class SearchCriteria(BaseModel):
    """Search criteria for eBay scraping."""
    keyword: str = Field(..., min_length=1, max_length=200, description="Search keyword")
    marketplace: Marketplace = Field(default=Marketplace.EBAY_US, description="eBay marketplace")
    category_id: Optional[str] = Field(None, description="eBay category ID")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price filter")
    condition: Optional[ProductCondition] = Field(None, description="Item condition filter")
    sold_listings_only: bool = Field(default=False, description="Search only sold listings")
    free_shipping_only: bool = Field(default=False, description="Search only items with free shipping")
    date_range_days: int = Field(default=30, ge=1, le=365, description="Date range in days")
    max_results: int = Field(default=20, ge=1, le=100, description="Maximum results to return")

    @validator('max_price')
    def validate_price_range(cls, v, values):
        """Ensure max_price is greater than min_price if both are set."""
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v <= values['min_price']:
                raise ValueError('max_price must be greater than min_price')
        return v


class ScrapingResult(BaseModel):
    """Complete result of a scraping operation."""
    result_id: Optional[str] = Field(None, description="Unique identifier for storage")
    criteria: SearchCriteria = Field(..., description="Original search criteria")
    products: List[Product] = Field(default_factory=list, description="Scraped products")
    market_analysis: Optional[MarketAnalysis] = Field(None, description="Market analysis data")
    status: ScrapingStatus = Field(default=ScrapingStatus.PENDING)
    error_message: Optional[str] = Field(None, description="Error message if failed")
    scraping_duration: Optional[float] = Field(None, ge=0, description="Duration in seconds")
    captcha_status: CaptchaStatus = Field(default=CaptchaStatus.NOT_DETECTED)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)
    
    @property
    def success(self) -> bool:
        """Whether the scraping operation was successful."""
        return self.status == ScrapingStatus.COMPLETED and len(self.products) > 0


class UserAgentHealthRecord(BaseModel):
    """Health record for a user agent."""
    user_agent: str = Field(..., description="User agent string")
    health_status: UserAgentHealth = Field(default=UserAgentHealth.HEALTHY)
    detection_count: int = Field(default=0, ge=0, description="Number of detections")
    last_detection: Optional[datetime] = Field(None, description="Last detection timestamp")
    last_success: Optional[datetime] = Field(None, description="Last successful use")
    consecutive_failures: int = Field(default=0, ge=0, description="Consecutive failures")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CaptchaEvent(BaseModel):
    """Event for CAPTCHA detection and handling."""
    event_id: str = Field(..., description="Unique event identifier")
    result_id: str = Field(..., description="Associated scraping result ID")
    captcha_type: str = Field(..., description="Type of CAPTCHA detected")
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    status: CaptchaStatus = Field(default=CaptchaStatus.DETECTED)
    page_url: str = Field(..., description="URL where CAPTCHA was detected")
    solved_at: Optional[datetime] = Field(None, description="When CAPTCHA was solved")
    manual_intervention_required: bool = Field(default=True)


class ExportRequest(BaseModel):
    """Request for exporting scraping results."""
    result_id: str = Field(..., description="Scraping result to export")
    format: ExportFormat = Field(..., description="Export format")
    include_images: bool = Field(default=False, description="Include product images")
    include_seller_info: bool = Field(default=True, description="Include seller information")
    include_market_analysis: bool = Field(default=True, description="Include market analysis")


class DatabaseScrape(BaseModel):
    """Database record for a scraping operation."""
    id: Optional[int] = Field(None, description="Primary key")
    result_id: str = Field(..., description="Unique result identifier")
    keyword: str = Field(..., description="Search keyword")
    marketplace: str = Field(..., description="eBay marketplace")
    total_products: int = Field(..., ge=0, description="Total products found")
    status: str = Field(..., description="Scraping status")
    duration: Optional[float] = Field(None, description="Scraping duration")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)


class DatabaseProduct(BaseModel):
    """Database record for a product."""
    id: Optional[int] = Field(None, description="Primary key")
    scrape_id: int = Field(..., description="Foreign key to scrape")
    item_id: str = Field(..., description="eBay item ID")
    title: str = Field(..., description="Product title")
    price: float = Field(..., description="Product price")
    condition: str = Field(..., description="Product condition")
    sold_count: Optional[int] = Field(None, description="Items sold")
    seller_name: Optional[str] = Field(None, description="Seller name")
    marketplace: str = Field(..., description="Source marketplace")
    item_url: str = Field(..., description="eBay item URL")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DatabaseSeller(BaseModel):
    """Database record for a seller."""
    id: Optional[int] = Field(None, description="Primary key")
    seller_name: str = Field(..., description="Seller username")
    feedback_score: Optional[int] = Field(None, description="Feedback score")
    feedback_percentage: Optional[float] = Field(None, description="Positive feedback %")
    total_sold_items: int = Field(default=0, description="Total items sold")
    marketplace: str = Field(..., description="Primary marketplace")
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class BotDetectionEvent(BaseModel):
    """Event logged when bot detection measures are triggered."""
    event_type: str = Field(..., description="Type of bot detection event")
    url: str = Field(..., description="URL where event occurred")
    response_code: Optional[int] = Field(None, description="HTTP response code")
    captcha_detected: bool = Field(default=False)
    security_measure_detected: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_agent: Optional[str] = Field(None, description="User agent used")
    retry_count: int = Field(default=0, ge=0, description="Number of retries attempted") 