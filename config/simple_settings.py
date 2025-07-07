"""
Simplified Settings for Quick Startup

A simplified configuration that works with Pydantic v2.
"""

from typing import Dict, Any


class SimpleSettings:
    """Simple settings class without Pydantic validation for quick startup."""
    
    def __init__(self):
        # Application settings
        self.app = AppSettings()
        self.web_server = WebServerSettings()
        self.scraping = ScrapingSettings() 
        self.bot_protection = BotProtectionSettings()
        self.retry = RetrySettings()
        self.logging = LoggingSettings()
        self.storage = StorageSettings()
        self.playwright = PlaywrightSettings()
    
    def get_scraping_config(self) -> Dict[str, Any]:
        """Get scraping configuration as dictionary."""
        return {
            'max_concurrent_requests': self.scraping.max_concurrent_requests,
            'request_timeout': self.scraping.request_timeout,
            'ebay_base_url': self.scraping.ebay_base_url
        }
    
    def get_bot_protection_config(self) -> Dict[str, Any]:
        """Get bot protection configuration as dictionary."""
        return {
            'min_delay': self.bot_protection.min_delay,
            'max_delay': self.bot_protection.max_delay,
            'user_agent_list': self.bot_protection.user_agent_list
        }
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration as dictionary."""
        return {
            'max_retries': self.retry.max_retries,
            'base_backoff': self.retry.base_backoff,
            'max_backoff': self.retry.max_backoff,
            'backoff_factor': self.retry.backoff_factor
        }


class AppSettings:
    """Application settings."""
    def __init__(self):
        self.app_name = "eBay Scraper"
        self.app_version = "1.0.0"
        self.environment = "development"
        self.use_mock_data = False  # Disabled by default for production enforcement


class WebServerSettings:
    """Web server settings."""
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 8000
        self.debug = True
        self.secret_key = "dev-secret-key"
        self.api_prefix = "/api/v1"
        self.enable_cors = True


class ScrapingSettings:
    """Scraping settings."""
    def __init__(self):
        self.max_concurrent_requests = 3
        self.request_timeout = 30.0
        self.ebay_base_url = "https://www.ebay.com"


class BotProtectionSettings:
    """Bot protection settings."""
    def __init__(self):
        self.min_delay = 1.0
        self.max_delay = 5.0
        self.scroll_probability = 0.7
        self.mouse_move_probability = 0.8
        self.user_agent_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]


class RetrySettings:
    """Retry settings."""
    def __init__(self):
        self.max_retries = 3
        self.base_backoff = 1.0
        self.max_backoff = 30.0
        self.backoff_factor = 2.0


class LoggingSettings:
    """Logging settings."""
    def __init__(self):
        self.level = "INFO"
        self.format = "json"
        self.log_to_file = True
        self.log_to_console = True
        self.log_file_path = "logs/ebay_scraper.log"
        self.max_file_size = 10485760
        self.backup_count = 5
        self.include_timestamp = True
        self.include_level = True
        self.include_module = True
        self.include_function = True
        self.console_level = "INFO"


class StorageSettings:
    """Storage settings."""
    def __init__(self):
        self.output_directory = "output"


class PlaywrightSettings:
    """Playwright settings."""
    def __init__(self):
        self.browser_type = "chromium"
        self.headless = True


# Global settings instance
settings = SimpleSettings() 