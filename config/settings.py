"""
Configuration Settings

Centralized configuration management using Pydantic settings.
Supports environment variables and multiple configuration sources.
"""

from typing import List, Dict, Any, Optional
from pydantic import Field, validator, ConfigDict
from pydantic_settings import BaseSettings
from pathlib import Path


class ScrapingConfig(BaseSettings):
    """Configuration for scraping operations."""
    model_config = ConfigDict(
        env_prefix="SCRAPING_",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Basic scraping settings
    max_concurrent_requests: int = Field(default=3, ge=1, le=10)
    request_timeout: float = Field(default=30.0, ge=5.0, le=120.0)
    page_load_timeout: float = Field(default=30.0, ge=5.0, le=120.0)
    
    # eBay specific settings
    ebay_base_url: str = Field(default="https://www.ebay.com")
    terapeak_base_url: str = Field(default="https://www.ebay.com/sch/research")
    
    # Default search settings
    default_max_results: int = Field(default=20, ge=1, le=100)
    default_date_range_days: int = Field(default=30, ge=1, le=365)


class BotProtectionConfig(BaseSettings):
    """Configuration for bot protection measures."""
    model_config = ConfigDict(
        env_prefix="BOT_PROTECTION_",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Timing settings
    min_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    max_delay: float = Field(default=5.0, ge=1.0, le=30.0)
    jitter_factor: float = Field(default=0.3, ge=0.0, le=1.0)
    
    # Behavior simulation
    mouse_move_probability: float = Field(default=0.8, ge=0.0, le=1.0)
    scroll_probability: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # User agent rotation
    rotate_user_agents: bool = Field(default=True)
    user_agent_list: List[str] = Field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
    ])
    
    # Detection handling
    captcha_retry_attempts: int = Field(default=3, ge=1, le=10)
    security_measure_backoff: float = Field(default=60.0, ge=10.0, le=300.0)


class RetryConfig(BaseSettings):
    """Configuration for retry logic."""
    
    max_retries: int = Field(default=3, ge=1, le=10)
    base_backoff: float = Field(default=1.0, ge=0.1, le=10.0)
    max_backoff: float = Field(default=30.0, ge=1.0, le=300.0)
    backoff_factor: float = Field(default=2.0, ge=1.0, le=5.0)
    
    # Specific retry settings for different error types
    rate_limit_retries: int = Field(default=5, ge=1, le=15)
    rate_limit_backoff: float = Field(default=60.0, ge=10.0, le=600.0)
    
    network_error_retries: int = Field(default=3, ge=1, le=10)
    network_error_backoff: float = Field(default=5.0, ge=1.0, le=60.0)
    
    class Config:
        env_prefix = "RETRY_"
        case_sensitive = False


class WebServerConfig(BaseSettings):
    """Configuration for the web server."""
    
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=5000, ge=1000, le=65535)
    debug: bool = Field(default=False)
    
    # API settings
    api_prefix: str = Field(default="/api/v1")
    enable_cors: bool = Field(default=True)
    
    # Session settings
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    session_timeout: int = Field(default=3600, ge=300, le=86400)  # 1 hour default
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)
    
    class Config:
        env_prefix = "WEB_"
        case_sensitive = False


class LoggingConfig(BaseSettings):
    """Configuration for logging."""
    
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = Field(default="json")  # json or text
    
    # File logging
    log_to_file: bool = Field(default=True)
    log_file_path: str = Field(default="logs/ebay_scraper.log")
    max_file_size: int = Field(default=10485760, ge=1048576)  # 10MB default
    backup_count: int = Field(default=5, ge=1, le=20)
    
    # Console logging
    log_to_console: bool = Field(default=True)
    console_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    
    # Structured logging fields
    include_timestamp: bool = Field(default=True)
    include_level: bool = Field(default=True)
    include_module: bool = Field(default=True)
    include_function: bool = Field(default=True)
    
    class Config:
        env_prefix = "LOG_"
        case_sensitive = False


class StorageConfig(BaseSettings):
    """Configuration for data storage."""
    
    # File storage settings
    output_directory: str = Field(default="output")
    results_filename_pattern: str = Field(default="scraping_results_{timestamp}.json")
    
    # Data retention
    max_results_age_days: int = Field(default=30, ge=1, le=365)
    auto_cleanup_enabled: bool = Field(default=True)
    
    # Compression
    compress_results: bool = Field(default=True)
    compression_level: int = Field(default=6, ge=1, le=9)
    
    class Config:
        env_prefix = "STORAGE_"
        case_sensitive = False


class PlaywrightConfig(BaseSettings):
    """Configuration for Playwright browser automation."""
    
    # Browser settings
    browser_type: str = Field(default="chromium", pattern="^(chromium|firefox|webkit)$")
    headless: bool = Field(default=True)
    
    # Browser launch options
    browser_args: List[str] = Field(default_factory=lambda: [
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",  # For faster loading
        "--disable-javascript",  # Can be enabled per page as needed
    ])
    
    # Viewport settings
    viewport_width: int = Field(default=1280, ge=800, le=1920)
    viewport_height: int = Field(default=720, ge=600, le=1080)
    
    # Context settings
    ignore_https_errors: bool = Field(default=True)
    user_data_dir: Optional[str] = Field(default=None)
    
    # Authentication
    ebay_state_file: str = Field(default="ebay_state.json")
    
    class Config:
        env_prefix = "PLAYWRIGHT_"
        case_sensitive = False


class AppConfig(BaseSettings):
    """Main application configuration."""
    
    # Application metadata
    app_name: str = Field(default="eBay Scraper")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    
    # Production enforcement flags
    use_mock_data: bool = Field(default=False, description="Whether to allow mock data services (disabled for production)")
    
    # Feature flags
    enable_terapeak: bool = Field(default=True)
    enable_fallback_scraping: bool = Field(default=True)
    enable_bot_protection: bool = Field(default=True)
    enable_metrics: bool = Field(default=True)
    
    # Resource limits
    max_concurrent_operations: int = Field(default=5, ge=1, le=20)
    operation_timeout: float = Field(default=300.0, ge=60.0, le=1800.0)  # 5 minutes default
    
    class Config:
        env_prefix = "APP_"
        case_sensitive = False
        env_file = ".env"


class Settings:
    """
    Main settings container that aggregates all configuration sections.
    
    This class follows the composition pattern to organize related settings
    and provides a single entry point for all configuration.
    """
    
    def __init__(self):
        """Initialize all configuration sections."""
        self.app = AppConfig()
        self.scraping = ScrapingConfig()
        self.bot_protection = BotProtectionConfig()
        self.retry = RetryConfig()
        self.web_server = WebServerConfig()
        self.logging = LoggingConfig()
        self.storage = StorageConfig()
        self.playwright = PlaywrightConfig()
        
        # Ensure required directories exist
        self._create_directories()
    
    def _create_directories(self) -> None:
        """Create required directories if they don't exist."""
        dirs_to_create = [
            self.storage.output_directory,
            Path(self.logging.log_file_path).parent,
        ]
        
        for directory in dirs_to_create:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_scraping_config(self) -> Dict[str, Any]:
        """Get scraping configuration as dictionary."""
        return self.scraping.dict()
    
    def get_bot_protection_config(self) -> Dict[str, Any]:
        """Get bot protection configuration as dictionary."""
        return self.bot_protection.dict()
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration as dictionary."""
        return self.retry.dict()
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app.environment == "development"


# Global settings instance
settings = Settings() 