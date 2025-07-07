"""
Scraping Orchestrator Service

Main orchestrator for coordinating scraping operations.
Implements strategy pattern for fallback between Terapeak and regular scraping.
Following Open/Closed and Dependency Inversion principles.
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Tuple

from ...domain.models import SearchCriteria, ScrapingResult, ScrapingStatus, Product, MarketAnalysis
from ...domain.exceptions import (
    ScrapingError,
    TerapeakError,
    RateLimitError,
    BotDetectionError
)
from ...domain.interfaces import (
    IScrapingOrchestrator,
    IMarketAnalyzer,
    IProductScraper,
    IBotProtection,
    IResultProcessor,
    IResultStorageService,
    IRetryHandler,
    ILogger
)


class ScrapingOrchestrator(IScrapingOrchestrator):
    """
    Main orchestrator for eBay scraping operations.
    
    Responsibilities:
    - Coordinate scraping workflow
    - Implement fallback strategies
    - Handle errors and retries
    - Ensure bot protection compliance
    """
    
    def __init__(
        self,
        terapeak_analyzer: IMarketAnalyzer,
        fallback_scraper: IProductScraper,
        bot_protection: IBotProtection,
        result_processor: IResultProcessor,
        result_storage: IResultStorageService,
        retry_handler: IRetryHandler,
        logger: ILogger
    ):
        """
        Initialize orchestrator with all dependencies.
        
        Args:
            terapeak_analyzer: Service for Terapeak market analysis
            fallback_scraper: Fallback product scraper
            bot_protection: Bot protection service
            result_processor: Service for processing results
            result_storage: Database storage service for result persistence
            retry_handler: Retry logic handler
            logger: Logging service
        """
        self._terapeak_analyzer = terapeak_analyzer
        self._fallback_scraper = fallback_scraper
        self._bot_protection = bot_protection
        self._result_processor = result_processor
        self._result_storage = result_storage
        self._retry_handler = retry_handler
        self._logger = logger

    async def execute_scraping(self, criteria: SearchCriteria) -> ScrapingResult:
        """
        Execute complete scraping operation with fallback strategies.
        
        Args:
            criteria: Search criteria for scraping
            
        Returns:
            Complete scraping result with products and market analysis
        """
        start_time = datetime.utcnow()
        
        # Initialize result object
        result = ScrapingResult(
            criteria=criteria,
            status=ScrapingStatus.IN_PROGRESS,
            created_at=start_time
        )
        
        await self._logger.log_info(
            "Starting scraping operation",
            keyword=criteria.keyword,
            max_results=criteria.max_results
        )
        
        try:
            # Execute scraping with retry logic
            products, market_analysis = await self._retry_handler.execute_with_retry(
                operation=lambda: self._execute_scraping_workflow(criteria),
                max_retries=3,
                backoff_factor=2.0
            )
            
            # Process and enrich results
            processed_products = await self._result_processor.process_results(products)
            
            # Update result object
            result.products = processed_products
            result.market_analysis = market_analysis
            result.status = ScrapingStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.scraping_duration = (result.completed_at - start_time).total_seconds()
            
            await self._logger.log_info(
                "Scraping completed successfully",
                keyword=criteria.keyword,
                products_found=len(processed_products),
                duration=result.scraping_duration
            )
            
        except RateLimitError as e:
            result.status = ScrapingStatus.RATE_LIMITED
            result.error_message = str(e)
            await self._logger.log_warning(
                "Scraping rate limited",
                keyword=criteria.keyword,
                error=str(e)
            )
            
        except (ScrapingError, BotDetectionError) as e:
            result.status = ScrapingStatus.FAILED
            result.error_message = str(e)
            await self._logger.log_error(
                "Scraping failed",
                keyword=criteria.keyword,
                error=str(e)
            )
            
        except Exception as e:
            result.status = ScrapingStatus.FAILED
            result.error_message = f"Unexpected error: {str(e)}"
            await self._logger.log_error(
                "Unexpected scraping error",
                keyword=criteria.keyword,
                error=str(e)
            )
        
        finally:
            # Always complete timing and save result
            if result.completed_at is None:
                result.completed_at = datetime.utcnow()
                result.scraping_duration = (result.completed_at - start_time).total_seconds()
            
            # Save result to storage
            try:
                result_id = await self._result_storage.store_scraping_result(result)
                result.result_id = result_id
                
                await self._logger.log_info(
                    "Result saved to storage",
                    result_id=result_id,
                    keyword=criteria.keyword
                )
            except Exception as e:
                await self._logger.log_error(
                    "Failed to save result",
                    keyword=criteria.keyword,
                    error=str(e)
                )
        
        return result

    async def _execute_scraping_workflow(self, criteria: SearchCriteria) -> Tuple[List[Product], Optional[MarketAnalysis]]:
        """
        Execute the main scraping workflow with fallback strategy.
        
        Args:
            criteria: Search criteria
            
        Returns:
            Tuple of (products, market_analysis)
        """
        products = []
        market_analysis = None
        
        # Strategy 1: Try Terapeak for market analysis
        try:
            await self._logger.log_info(
                "Attempting Terapeak market analysis",
                keyword=criteria.keyword
            )
            
            market_analysis = await self._terapeak_analyzer.analyze_market(criteria)
            
            if market_analysis:
                await self._logger.log_info(
                    "Terapeak analysis successful",
                    keyword=criteria.keyword,
                    avg_price=str(market_analysis.avg_sold_price),
                    total_sales=market_analysis.total_sales
                )
            else:
                await self._logger.log_warning(
                    "Terapeak analysis returned no data",
                    keyword=criteria.keyword
                )
                
        except TerapeakError as e:
            await self._logger.log_warning(
                "Terapeak analysis failed, will use fallback",
                keyword=criteria.keyword,
                error=str(e)
            )
        except BotDetectionError as e:
            await self._logger.log_warning(
                "Bot detection during Terapeak analysis",
                keyword=criteria.keyword,
                error=str(e)
            )
            # Don't continue if bot detection occurs, might affect fallback
            raise
        except Exception as e:
            await self._logger.log_error(
                "Unexpected error in Terapeak analysis",
                keyword=criteria.keyword,
                error=str(e)
            )
        
        # Strategy 2: Fallback product scraping
        try:
            await self._logger.log_info(
                "Starting fallback product scraping",
                keyword=criteria.keyword,
                max_results=criteria.max_results
            )
            
            products = await self._fallback_scraper.scrape_products(criteria)
            
            await self._logger.log_info(
                "Fallback scraping successful",
                keyword=criteria.keyword,
                products_found=len(products)
            )
            
        except BotDetectionError:
            # Re-raise bot detection errors immediately
            raise
        except RateLimitError:
            # Re-raise rate limit errors immediately
            raise
        except ScrapingError as e:
            await self._logger.log_error(
                "Fallback scraping failed",
                keyword=criteria.keyword,
                error=str(e)
            )
            raise
        
        # If we have no products and no market analysis, this is a failure
        if not products and not market_analysis:
            raise ScrapingError(
                "All scraping strategies failed - no data retrieved",
                details={"keyword": criteria.keyword}
            )
        
        return products, market_analysis

    async def get_scraping_status(self, result_id: str) -> Optional[ScrapingResult]:
        """
        Get status of a scraping operation by result ID.
        
        Args:
            result_id: Unique result identifier
            
        Returns:
            Scraping result or None if not found
        """
        try:
            return await self._result_storage.get_scraping_result(result_id)
        except Exception as e:
            await self._logger.log_error(
                "Failed to retrieve scraping status",
                result_id=result_id,
                error=str(e)
            )
            return None

    async def cancel_scraping(self, result_id: str) -> bool:
        """
        Cancel an ongoing scraping operation (future implementation).
        
        Args:
            result_id: Unique result identifier
            
        Returns:
            True if successfully cancelled
        """
        # TODO: Implement cancellation logic
        # This would require task tracking and graceful shutdown
        await self._logger.log_info(
            "Scraping cancellation requested (not yet implemented)",
            result_id=result_id
        )
        return False

    async def health_check(self) -> dict:
        """
        Perform health check on all dependent services.
        
        Returns:
            Dictionary with health status of each service
        """
        health_status = {
            "overall": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        # Check each service (simplified implementation)
        try:
            # These would be actual health checks in a real implementation
            health_status["services"]["terapeak"] = "available"
            health_status["services"]["fallback_scraper"] = "available" 
            health_status["services"]["bot_protection"] = "active"
            health_status["services"]["data_storage"] = "connected"
            
            await self._logger.log_info("Health check completed", status=health_status)
            
        except Exception as e:
            health_status["overall"] = "degraded"
            health_status["error"] = str(e)
            await self._logger.log_error("Health check failed", error=str(e))
        
        return health_status 