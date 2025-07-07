"""
Configuration Service

Provides access to application configuration.
"""

from typing import Dict, Any

from ..domain.interfaces import IConfiguration
from config.simple_settings import settings


class ConfigurationService(IConfiguration):
    """Service for accessing application configuration."""
    
    def get_scraping_config(self) -> Dict[str, Any]:
        """Get scraping configuration settings."""
        return settings.get_scraping_config()
    
    def get_bot_protection_config(self) -> Dict[str, Any]:
        """Get bot protection configuration settings."""
        return settings.get_bot_protection_config()
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry and backoff configuration."""
        return settings.get_retry_config() 