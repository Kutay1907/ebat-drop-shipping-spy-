"""
Dependency Injection Container

Centralized dependency management following Dependency Inversion Principle.
Provides clean separation of concerns and easy testing.
"""

from typing import Dict, Any, Optional
import asyncio

from ..domain.interfaces import (
    ILogger,
    IUserAgentRotator,
    IBotProtection,
    IRetryHandler,
    IConfiguration,
    IDataStorage,
    IResultProcessor,
    IMarketAnalyzer,
    IProductScraper,
    IScrapingOrchestrator,
    IResultStorageService,
    IEbayLoginService,
    ICaptchaHandlerService,
    IUserAgentHealthTracker,
    IExportService
)
from ..domain.exceptions import ConfigurationError
from ..application.services.keyword_input_service import KeywordInputService
from ..application.services.scraping_orchestrator import ScrapingOrchestrator
from .bot_protection import BotProtectionService
from .logging_service import StructuredLogger
from .user_agent_rotator import UserAgentRotator
from .retry_handler import RetryHandler
from .configuration_service import ConfigurationService
from .storage_service import FileStorageService
from .result_processor import ResultProcessor
from .database_storage import DatabaseStorageService
from .ebay_login_service import EbayLoginService
from .captcha_handler_service import CaptchaHandlerService
from .user_agent_health_tracker import UserAgentHealthTracker
from .export_service import ExportService
from .cli_service import CLIService

# Real service implementations
from .terapeak_analyzer import TerapeakAnalyzer
from .fallback_scraper import FallbackScraper

from config.simple_settings import settings


class DependencyContainer:
    """
    Dependency injection container implementing the Service Locator pattern.
    
    This container manages the lifecycle and dependencies of all services,
    ensuring proper initialization order and dependency satisfaction.
    """
    
    def __init__(self):
        """Initialize the container and register all services."""
        self._services: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all services with proper dependency injection."""
        if self._initialized:
            return
        
        # Core infrastructure services (no dependencies)
        self._services['configuration'] = ConfigurationService()
        self._services['logger'] = StructuredLogger(settings.logging)
        self._services['user_agent_rotator'] = UserAgentRotator(settings.bot_protection)
        self._services['retry_handler'] = RetryHandler(settings.retry)
        
        # ✅ CRITICAL FIX: Check production enforcement after logger is available
        await self._validate_production_configuration()
        
        # Enhanced user agent management
        self._services['user_agent_health_tracker'] = UserAgentHealthTracker(
            self._services['logger']
        )
        
        # Storage services
        self._services['data_storage'] = FileStorageService(
            settings.storage,
            self._services['logger']
        )
        
        # Database storage service
        db_path = "data/ebay_scraper.db"
        self._services['database_storage'] = DatabaseStorageService(
            db_path,
            self._services['logger']
        )
        await self._services['database_storage'].initialize()
        
        # eBay login service
        self._services['ebay_login_service'] = EbayLoginService(
            self._services['logger'],
            headless=True
        )
        
        # CAPTCHA handler service
        self._services['captcha_handler'] = CaptchaHandlerService(
            self._services['logger']
        )
        
        # Export service
        self._services['export_service'] = ExportService(
            self._services['logger']
        )
        
        # Bot protection (depends on user agent rotator, health tracker, and logger)
        self._services['bot_protection'] = BotProtectionService(
            self._services['user_agent_rotator'],
            self._services['logger'],
            settings.bot_protection.min_delay,
            settings.bot_protection.max_delay,
            settings.bot_protection.scroll_probability,
            settings.bot_protection.mouse_move_probability
        )
        
        # Processing services
        self._services['result_processor'] = ResultProcessor(
            self._services['logger']
        )
        
        # Real scraping services (production-ready implementations)
        await self._initialize_scraping_services()
        
        # Application services
        self._services['keyword_input_service'] = KeywordInputService(
            self._services['logger']
        )
        
        # Main orchestrator (depends on all scraping services)
        self._services['scraping_orchestrator'] = ScrapingOrchestrator(
            self._services['terapeak_analyzer'],
            self._services['fallback_scraper'],
            self._services['bot_protection'],
            self._services['result_processor'],
            self._services['database_storage'],
            self._services['retry_handler'],
            self._services['logger']
        )
        
        # CLI service (depends on storage, export, and orchestrator)
        self._services['cli_service'] = CLIService(
            self._services['database_storage'],
            self._services['export_service'],
            self._services['scraping_orchestrator'],
            self._services['logger']
        )
        
        self._initialized = True
        
        # Log production mode status
        if not settings.app.use_mock_data:
            await self._services['logger'].log_info(
                "🚀 Production mode: All services are real, no mock data allowed",
                use_mock_data=settings.app.use_mock_data,
                environment=settings.app.environment
            )
        
        await self._services['logger'].log_info(
            "Dependency container initialized successfully",
            services_count=len(self._services),
            production_mode=not settings.app.use_mock_data
        )
    
    async def _validate_production_configuration(self) -> None:
        """Validate that production configuration is correct."""
        if not settings.app.use_mock_data:
            # Production mode - ensure all critical dependencies are available
            try:
                # Check if Playwright is available for real scraping
                import playwright
                await self._services['logger'].log_info(
                    "✅ Playwright dependency verified for production mode"
                )
            except ImportError:
                raise ConfigurationError(
                    "❌ Production mode requires Playwright for real scraping. "
                    "Please install: pip install playwright && playwright install chromium",
                    config_key="playwright_dependency"
                )
    
    async def _initialize_scraping_services(self) -> None:
        """Initialize scraping services based on configuration."""
        if settings.app.use_mock_data:
            # Development mode with mock data allowed - import dynamically
            await self._services['logger'].log_info(
                "⚠️  Development mode: Using mock services",
                use_mock_data=settings.app.use_mock_data
            )
            
            # Dynamic import of mock services only when needed
            from .mock_services import MockTerapeakAnalyzer, MockFallbackScraper
            
            self._services['terapeak_analyzer'] = MockTerapeakAnalyzer(
                self._services['logger']
            )
            self._services['fallback_scraper'] = MockFallbackScraper(
                self._services['bot_protection'],
                self._services['logger']
            )
        else:
            # Production mode - use only real services
            await self._services['logger'].log_info(
                "🔥 Production mode: Initializing real scraping services",
                use_mock_data=settings.app.use_mock_data
            )
            
            try:
                # Initialize real Terapeak analyzer
                self._services['terapeak_analyzer'] = TerapeakAnalyzer(
                    self._services['logger'],
                    self._services['bot_protection'],
                    headless=True,
                    timeout=30.0
                )
                
                # Initialize real fallback scraper
                self._services['fallback_scraper'] = FallbackScraper(
                    self._services['bot_protection'],
                    self._services['logger'],
                    headless=True,
                    timeout=30.0
                )
                
                await self._services['logger'].log_info(
                    "✅ Real scraping services initialized successfully"
                )
                
                # ✅ CRITICAL FIX: Validate services in production
                await self._validate_scraping_services()
                
            except Exception as e:
                raise ConfigurationError(
                    f"❌ Failed to initialize real scraping services: {str(e)}. "
                    f"Set USE_MOCK_DATA=true for development mode.",
                    config_key="scraping_services"
                )
    
    async def _validate_scraping_services(self) -> None:
        """Validate that scraping services are properly initialized and functional."""
        if not settings.app.use_mock_data:
            await self._services['logger'].log_info("🔍 Validating production scraping services...")
            
            # Validate Terapeak analyzer
            terapeak = self._services['terapeak_analyzer']
            if "Mock" in terapeak.__class__.__name__:
                raise ConfigurationError(
                    "❌ Production mode detected mock Terapeak analyzer",
                    config_key="terapeak_service_validation"
                )
            
            # Validate Fallback scraper  
            fallback = self._services['fallback_scraper']
            if "Mock" in fallback.__class__.__name__:
                raise ConfigurationError(
                    "❌ Production mode detected mock fallback scraper", 
                    config_key="fallback_service_validation"
                )
            
            # Check that services have required methods
            if not hasattr(terapeak, 'analyze_market'):
                raise ConfigurationError(
                    "❌ Terapeak analyzer missing analyze_market method",
                    config_key="terapeak_method_validation"
                )
            
            if not hasattr(fallback, 'scrape_products'):
                raise ConfigurationError(
                    "❌ Fallback scraper missing scrape_products method",
                    config_key="fallback_method_validation"
                )
            
            await self._services['logger'].log_info("✅ Production scraping services validated successfully")
    
    async def _check_service_type_validation(self) -> None:
        """Validate that no mock services are active in production mode."""
        if not settings.app.use_mock_data:
            # Check for mock services
            mock_services_found = []
            
            for service_name, service in self._services.items():
                service_class_name = service.__class__.__name__
                if "Mock" in service_class_name:
                    mock_services_found.append(f"{service_name} ({service_class_name})")
            
            if mock_services_found:
                raise ConfigurationError(
                    f"❌ Production mode requires all services to be real. "
                    f"Mock services detected: {', '.join(mock_services_found)}",
                    config_key="production_enforcement"
                )
    
    def get_logger(self) -> ILogger:
        """Get the logging service."""
        return self._services['logger']
    
    def get_configuration(self) -> IConfiguration:
        """Get the configuration service."""
        return self._services['configuration']
    
    def get_user_agent_rotator(self) -> IUserAgentRotator:
        """Get the user agent rotation service."""
        return self._services['user_agent_rotator']
    
    def get_user_agent_health_tracker(self) -> IUserAgentHealthTracker:
        """Get the user agent health tracker service."""
        return self._services['user_agent_health_tracker']
    
    def get_bot_protection(self) -> IBotProtection:
        """Get the bot protection service."""
        return self._services['bot_protection']
    
    def get_retry_handler(self) -> IRetryHandler:
        """Get the retry handler service."""
        return self._services['retry_handler']
    
    def get_data_storage(self) -> IDataStorage:
        """Get the data storage service."""
        return self._services['data_storage']
    
    def get_database_storage(self) -> IResultStorageService:
        """Get the database storage service."""
        return self._services['database_storage']
    
    def get_ebay_login_service(self) -> IEbayLoginService:
        """Get the eBay login service."""
        return self._services['ebay_login_service']
    
    def get_captcha_handler(self) -> ICaptchaHandlerService:
        """Get the CAPTCHA handler service."""
        return self._services['captcha_handler']
    
    def get_export_service(self) -> IExportService:
        """Get the export service."""
        return self._services['export_service']
    
    def get_result_processor(self) -> IResultProcessor:
        """Get the result processor service."""
        return self._services['result_processor']
    
    def get_terapeak_analyzer(self) -> IMarketAnalyzer:
        """Get the Terapeak analyzer service."""
        service = self._services['terapeak_analyzer']
        self._validate_service_in_production(service, 'terapeak_analyzer')
        return service
    
    def get_fallback_scraper(self) -> IProductScraper:
        """Get the fallback scraper service."""
        service = self._services['fallback_scraper']
        self._validate_service_in_production(service, 'fallback_scraper')
        return service
    
    def get_keyword_input_service(self) -> KeywordInputService:
        """Get the keyword input service."""
        return self._services['keyword_input_service']
    
    def get_scraping_orchestrator(self) -> IScrapingOrchestrator:
        """Get the main scraping orchestrator."""
        return self._services['scraping_orchestrator']
    
    def get_cli_service(self) -> CLIService:
        """Get the CLI service."""
        return self._services['cli_service']
    
    def _validate_service_in_production(self, service: Any, service_name: str) -> None:
        """Validate that service is not a mock in production mode."""
        if not settings.app.use_mock_data:
            service_class_name = service.__class__.__name__
            if "Mock" in service_class_name:
                raise ConfigurationError(
                    f"❌ Production mode requires all services to be real. "
                    f"Mock service detected: {service_name} ({service_class_name})",
                    config_key="production_enforcement"
                )
            
            # ✅ Additional runtime validation
            self._services['logger'].log_info(
                f"✅ Service validated in production: {service_name} -> {service_class_name}",
                service_name=service_name,
                service_class=service_class_name,
                is_mock=False
            )
    
    async def cleanup(self) -> None:
        """Clean up all services and resources."""
        if not self._initialized:
            return
        
        await self._services['logger'].log_info("Cleaning up dependency container")
        
        # Clean up services in reverse order of initialization
        cleanup_order = [
            'cli_service',
            'scraping_orchestrator',
            'keyword_input_service',
            'fallback_scraper',
            'terapeak_analyzer',
            'result_processor',
            'bot_protection',
            'export_service',
            'captcha_handler',
            'ebay_login_service',
            'database_storage',
            'data_storage',
            'user_agent_health_tracker',
            'retry_handler',
            'user_agent_rotator',
            'logger',
            'configuration'
        ]
        
        for service_name in cleanup_order:
            service = self._services.get(service_name)
            if service and hasattr(service, 'cleanup'):
                try:
                    await service.cleanup()
                except Exception as e:
                    print(f"Error cleaning up {service_name}: {e}")
        
        self._services.clear()
        self._initialized = False


# Global container instance
container = DependencyContainer() 