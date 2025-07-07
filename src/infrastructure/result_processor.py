"""
Result Processor Service

Processes and enriches scraping results.
"""

from typing import List
from decimal import Decimal

from ..domain.interfaces import IResultProcessor, ILogger
from ..domain.models import Product


class ResultProcessor(IResultProcessor):
    """
    Service for processing and enriching product data.
    
    Features:
    - Data validation
    - Price normalization
    - Data enrichment
    """
    
    def __init__(self, logger: ILogger):
        """
        Initialize result processor.
        
        Args:
            logger: Logging service
        """
        self.logger = logger
    
    async def process_results(self, products: List[Product]) -> List[Product]:
        """
        Process and enrich product data.
        
        Args:
            products: Raw product data
            
        Returns:
            Enriched product data
        """
        await self.logger.log_info(
            "Processing results",
            product_count=len(products)
        )
        
        processed_products = []
        
        for product in products:
            try:
                # Process individual product
                processed_product = await self._process_product(product)
                if processed_product:
                    processed_products.append(processed_product)
            except Exception as e:
                await self.logger.log_error(
                    "Failed to process product",
                    product_id=product.item_id,
                    error=str(e)
                )
                # Continue with other products
                continue
        
        await self.logger.log_info(
            "Results processed",
            original_count=len(products),
            processed_count=len(processed_products)
        )
        
        return processed_products
    
    async def _process_product(self, product: Product) -> Product:
        """
        Process individual product data.
        
        Args:
            product: Product to process
            
        Returns:
            Processed product
        """
        # For now, just return the product as-is
        # In a real implementation, this could:
        # - Normalize price data
        # - Validate URLs
        # - Clean up text fields
        # - Add calculated metrics
        # - Fetch additional data
        
        return product 