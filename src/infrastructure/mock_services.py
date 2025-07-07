"""
Mock Services

Mock implementations for testing and demonstration.
⚠️ WARNING: These services are for development only and should not be used in production.
"""

import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from config.simple_settings import settings
from ..domain.exceptions import ConfigurationError

# Production enforcement check
if not settings.app.use_mock_data:
    raise ConfigurationError(
        "❌ Mock services cannot be imported in production mode. "
        "Set USE_MOCK_DATA=true for development or use real services.",
        config_key="mock_services_import"
    )

from ..domain.interfaces import IMarketAnalyzer, IProductScraper, IBotProtection, ILogger
from ..domain.models import (
    SearchCriteria, 
    MarketAnalysis, 
    Product, 
    TrendPoint, 
    PriceRange,
    ProductCondition
)


class MockTerapeakAnalyzer(IMarketAnalyzer):
    """
    Mock Terapeak analyzer for demonstration purposes.
    ⚠️ FOR DEVELOPMENT ONLY - NOT FOR PRODUCTION USE
    """
    
    def __init__(self, logger: ILogger):
        """Initialize mock analyzer."""
        self.logger = logger
        # Additional production check at instantiation
        if not settings.app.use_mock_data:
            raise ConfigurationError(
                "❌ MockTerapeakAnalyzer cannot be instantiated in production mode",
                config_key="mock_terapeak_instantiation"
            )
    
    async def analyze_market(self, criteria: SearchCriteria) -> Optional[MarketAnalysis]:
        """
        Analyze market data for given search criteria.
        
        Args:
            criteria: Search parameters for analysis
            
        Returns:
            Mock market analysis data
        """
        await self.logger.log_info(
            "⚠️ MOCK: Terapeak analysis started (DEVELOPMENT MODE)",
            keyword=criteria.keyword
        )
        
        # Simulate analysis delay
        await asyncio.sleep(random.uniform(1.0, 3.0))
        
        # Generate mock trend data
        trend_data = []
        base_date = datetime.utcnow() - timedelta(days=30)
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            trend_data.append(TrendPoint(
                date=date,
                avg_price=Decimal(str(round(random.uniform(10.0, 100.0), 2))),
                sales_volume=random.randint(10, 200),
                active_listings=random.randint(50, 500)
            ))
        
        # Create mock market analysis
        analysis = MarketAnalysis(
            keyword=criteria.keyword,
            avg_sold_price=Decimal(str(round(random.uniform(20.0, 80.0), 2))),
            price_range=PriceRange(
                min_price=Decimal("5.99"),
                max_price=Decimal("199.99")
            ),
            sell_through_rate=round(random.uniform(15.0, 85.0), 2),
            free_shipping_rate=round(random.uniform(40.0, 90.0), 2),
            seller_count=random.randint(10, 100),
            total_sales=random.randint(100, 2000),
            trend_data=trend_data
        )
        
        await self.logger.log_info(
            "⚠️ MOCK: Terapeak analysis completed (DEVELOPMENT MODE)",
            keyword=criteria.keyword,
            avg_price=str(analysis.avg_sold_price),
            total_sales=analysis.total_sales
        )
        
        return analysis


class MockFallbackScraper(IProductScraper):
    """
    Mock fallback scraper for demonstration purposes.
    ⚠️ FOR DEVELOPMENT ONLY - NOT FOR PRODUCTION USE
    """
    
    def __init__(self, bot_protection: IBotProtection, logger: ILogger):
        """Initialize mock scraper."""
        self.bot_protection = bot_protection
        self.logger = logger
        # Additional production check at instantiation
        if not settings.app.use_mock_data:
            raise ConfigurationError(
                "❌ MockFallbackScraper cannot be instantiated in production mode",
                config_key="mock_scraper_instantiation"
            )
    
    async def scrape_products(self, criteria: SearchCriteria) -> List[Product]:
        """
        Scrape products based on search criteria.
        
        Args:
            criteria: Search parameters and filters
            
        Returns:
            Mock list of scraped products
        """
        await self.logger.log_info(
            "⚠️ MOCK: Fallback scraping started (DEVELOPMENT MODE)",
            keyword=criteria.keyword,
            max_results=criteria.max_results
        )
        
        # Simulate scraping delay
        await asyncio.sleep(random.uniform(2.0, 5.0))
        
        products = []
        num_products = min(criteria.max_results, random.randint(5, 20))
        
        for i in range(num_products):
            product = Product(
                item_id=f"mock_{criteria.keyword}_{i}_{random.randint(1000, 9999)}",
                title=f"MOCK {criteria.keyword} Product {i+1}",
                price=Decimal(str(round(random.uniform(5.0, 150.0), 2))),
                condition=random.choice(list(ProductCondition)),
                sold_count=random.randint(0, 500) if random.random() > 0.3 else None,
                item_url=f"https://www.ebay.com/itm/mock{i}",
                image_url=f"https://example.com/image{i}.jpg" if random.random() > 0.2 else None,
                seller_name=f"mock_seller_{random.randint(1, 100)}",
                shipping_cost=Decimal(str(round(random.uniform(0.0, 15.0), 2))) if random.random() > 0.4 else None,
                free_shipping=random.random() > 0.6,
                location=random.choice(["California", "New York", "Texas", "Florida", "Unknown"]),
                listing_date=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            products.append(product)
        
        await self.logger.log_info(
            "⚠️ MOCK: Fallback scraping completed (DEVELOPMENT MODE)",
            keyword=criteria.keyword,
            products_found=len(products)
        )
        
        return products 