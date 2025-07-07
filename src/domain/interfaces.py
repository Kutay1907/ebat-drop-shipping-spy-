"""
Domain Interfaces

Abstract base classes and protocols defining contracts for services.
Following Interface Segregation and Dependency Inversion principles.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Protocol, AsyncGenerator, Any, Dict
from .models import (
    SearchCriteria,
    ScrapingResult,
    Product,
    MarketAnalysis,
    BotDetectionEvent
)


class IProductScraper(ABC):
    """Interface for product scraping services."""
    
    @abstractmethod
    async def scrape_products(self, criteria: SearchCriteria) -> List[Product]:
        """
        Scrape products based on search criteria.
        
        Args:
            criteria: Search parameters and filters
            
        Returns:
            List of scraped products
            
        Raises:
            ScrapingError: When scraping fails
            RateLimitError: When rate limited by eBay
        """
        pass


class IMarketAnalyzer(ABC):
    """Interface for market analysis services."""
    
    @abstractmethod
    async def analyze_market(self, criteria: SearchCriteria) -> Optional[MarketAnalysis]:
        """
        Analyze market data for given search criteria.
        
        Args:
            criteria: Search parameters for analysis
            
        Returns:
            Market analysis data or None if unavailable
        """
        pass


class IBotProtection(ABC):
    """Interface for bot detection and protection services."""
    
    @abstractmethod
    async def apply_protection(self, page) -> None:
        """
        Apply bot protection measures to a Playwright page.
        
        Args:
            page: Playwright page instance
        """
        pass
    
    @abstractmethod
    async def handle_detection(self, page, event: BotDetectionEvent) -> bool:
        """
        Handle detected bot protection measures.
        
        Args:
            page: Playwright page instance
            event: Bot detection event details
            
        Returns:
            True if successfully handled, False otherwise
        """
        pass
    
    @abstractmethod
    async def is_rate_limited(self, page) -> bool:
        """
        Check if current page indicates rate limiting.
        
        Args:
            page: Playwright page instance
            
        Returns:
            True if rate limited
        """
        pass


class IScrapingOrchestrator(ABC):
    """Interface for orchestrating complete scraping operations."""
    
    @abstractmethod
    async def execute_scraping(self, criteria: SearchCriteria) -> ScrapingResult:
        """
        Execute complete scraping operation with fallback strategies.
        
        Args:
            criteria: Search criteria
            
        Returns:
            Complete scraping result
        """
        pass


class IResultProcessor(ABC):
    """Interface for processing and enriching scraping results."""
    
    @abstractmethod
    async def process_results(self, products: List[Product]) -> List[Product]:
        """
        Process and enrich product data.
        
        Args:
            products: Raw product data
            
        Returns:
            Enriched product data
        """
        pass


class IDataStorage(ABC):
    """Interface for data persistence operations."""
    
    @abstractmethod
    async def save_result(self, result: ScrapingResult) -> str:
        """
        Save scraping result.
        
        Args:
            result: Scraping result to save
            
        Returns:
            Unique identifier for saved result
        """
        pass
    
    @abstractmethod
    async def get_result(self, result_id: str) -> Optional[ScrapingResult]:
        """
        Retrieve scraping result by ID.
        
        Args:
            result_id: Unique result identifier
            
        Returns:
            Scraping result or None if not found
        """
        pass


class IConfiguration(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def get_scraping_config(self) -> dict:
        """Get scraping configuration settings."""
        pass
    
    @abstractmethod
    def get_bot_protection_config(self) -> dict:
        """Get bot protection configuration settings."""
        pass
    
    @abstractmethod
    def get_retry_config(self) -> dict:
        """Get retry and backoff configuration."""
        pass


class ILogger(Protocol):
    """Protocol for logging services."""
    
    async def log_info(self, message: str, **kwargs) -> None:
        """Log informational message."""
        ...
    
    async def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        ...
    
    async def log_error(self, message: str, **kwargs) -> None:
        """Log error message."""
        ...
    
    async def log_bot_detection(self, event: BotDetectionEvent) -> None:
        """Log bot detection event."""
        ...


class IUserAgentRotator(ABC):
    """Interface for user agent rotation."""
    
    @abstractmethod
    def get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        pass
    
    @abstractmethod
    def get_mobile_user_agent(self) -> str:
        """Get a mobile user agent string."""
        pass


class IProxyManager(ABC):
    """Interface for proxy management (future extensibility)."""
    
    @abstractmethod
    async def get_proxy(self) -> Optional[str]:
        """Get next available proxy."""
        pass
    
    @abstractmethod
    async def mark_proxy_failed(self, proxy: str) -> None:
        """Mark proxy as failed."""
        pass


class IRetryHandler(ABC):
    """Interface for retry logic handling."""
    
    @abstractmethod
    async def execute_with_retry(
        self,
        operation,
        max_retries: int = 3,
        backoff_factor: float = 1.0
    ) -> Any:
        """
        Execute operation with retry logic.
        
        Args:
            operation: Async callable to execute
            max_retries: Maximum number of retries
            backoff_factor: Exponential backoff factor
            
        Returns:
            Operation result
        """
        pass


# Domain Events (for future event-driven architecture)
class IDomainEventPublisher(ABC):
    """Interface for publishing domain events."""
    
    @abstractmethod
    async def publish(self, event: dict) -> None:
        """Publish domain event."""
        pass


class IDomainEventHandler(ABC):
    """Interface for handling domain events."""
    
    @abstractmethod
    async def handle(self, event: dict) -> None:
        """Handle domain event."""
        pass


class IResultStorageService(ABC):
    """Interface for persistent storage of scraping results."""
    
    @abstractmethod
    async def store_scraping_result(self, result: ScrapingResult) -> str:
        """Store a complete scraping result and return unique ID."""
        pass
    
    @abstractmethod
    async def get_scraping_result(self, result_id: str) -> Optional[ScrapingResult]:
        """Retrieve scraping result by ID."""
        pass
    
    @abstractmethod
    async def get_scraping_history(
        self, 
        keyword: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ScrapingResult]:
        """Get historical scraping results with optional filtering."""
        pass
    
    @abstractmethod
    async def search_products(
        self,
        keyword: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 100
    ) -> List[Product]:
        """Search stored products with filtering."""
        pass


class IEbayLoginService(ABC):
    """Interface for eBay login automation."""
    
    @abstractmethod
    async def login(self, username: str, password: str) -> bool:
        """Perform headless login to eBay."""
        pass
    
    @abstractmethod
    async def handle_two_factor_auth(self, page) -> bool:
        """Handle 2FA if required during login."""
        pass
    
    @abstractmethod
    async def export_session_cookies(self, file_path: str) -> None:
        """Export session cookies to JSON file."""
        pass
    
    @abstractmethod
    async def is_logged_in(self) -> bool:
        """Check if current session is authenticated."""
        pass
    
    @abstractmethod
    async def refresh_session(self) -> bool:
        """Refresh existing session or re-login."""
        pass


class ICaptchaHandlerService(ABC):
    """Interface for CAPTCHA detection and handling."""
    
    @abstractmethod
    async def detect_captcha(self, page) -> bool:
        """Detect if CAPTCHA is present on the page."""
        pass
    
    @abstractmethod
    async def handle_captcha_manual(self, page, result_id: str) -> bool:
        """Handle CAPTCHA with manual intervention."""
        pass
    
    @abstractmethod
    async def wait_for_manual_solve(self, result_id: str, timeout: int = 300) -> bool:
        """Wait for user to manually solve CAPTCHA."""
        pass
    
    @abstractmethod
    async def mark_captcha_solved(self, result_id: str) -> None:
        """Mark CAPTCHA as solved by user."""
        pass


class IUserAgentHealthTracker(ABC):
    """Interface for tracking user agent health and rotation."""
    
    @abstractmethod
    async def track_detection_event(self, user_agent: str, event: BotDetectionEvent) -> None:
        """Track bot detection event for specific user agent."""
        pass
    
    @abstractmethod
    async def is_user_agent_tainted(self, user_agent: str) -> bool:
        """Check if user agent should be rotated out."""
        pass
    
    @abstractmethod
    async def get_healthy_user_agents(self) -> List[str]:
        """Get list of healthy user agents for rotation."""
        pass
    
    @abstractmethod
    async def reset_user_agent_health(self, user_agent: str) -> None:
        """Reset health status for user agent."""
        pass


class IExportService(ABC):
    """Interface for exporting scraping results in various formats."""
    
    @abstractmethod
    async def export_to_csv(self, result: ScrapingResult, file_path: str) -> None:
        """Export scraping result to CSV format."""
        pass
    
    @abstractmethod
    async def export_to_xlsx(self, result: ScrapingResult, file_path: str) -> None:
        """Export scraping result to Excel format."""
        pass
    
    @abstractmethod
    async def export_to_html(self, result: ScrapingResult, file_path: str) -> None:
        """Export scraping result to HTML format."""
        pass
    
    @abstractmethod
    async def get_export_data(self, result: ScrapingResult) -> Dict[str, Any]:
        """Get structured data for export."""
        pass


class IMarketplaceAdapter(ABC):
    """Interface for supporting multiple eBay marketplaces."""
    
    @abstractmethod
    async def get_marketplace_config(self, marketplace: str) -> Dict[str, Any]:
        """Get configuration for specific marketplace."""
        pass
    
    @abstractmethod
    async def build_search_url(self, criteria: SearchCriteria, marketplace: str) -> str:
        """Build search URL for specific marketplace."""
        pass
    
    @abstractmethod
    async def adapt_results(self, products: List[Product], marketplace: str) -> List[Product]:
        """Adapt product results for marketplace-specific formatting."""
        pass


class IDashboardService(ABC):
    """Interface for dashboard data aggregation."""
    
    @abstractmethod
    async def get_price_distribution(self, result: ScrapingResult) -> Dict[str, Any]:
        """Get price distribution data for charts."""
        pass
    
    @abstractmethod
    async def get_sold_count_histogram(self, result: ScrapingResult) -> Dict[str, Any]:
        """Get sold count histogram data."""
        pass
    
    @abstractmethod
    async def get_seller_analytics(self, result: ScrapingResult) -> Dict[str, Any]:
        """Get seller analytics data."""
        pass
    
    @abstractmethod
    async def get_market_trends(self, keyword: str, days: int = 30) -> Dict[str, Any]:
        """Get market trend data over time."""
        pass 