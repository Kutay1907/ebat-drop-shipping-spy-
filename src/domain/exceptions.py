"""
Domain Exceptions

Custom exceptions for the eBay scraper domain.
Following single responsibility principle - each exception has a specific purpose.
"""

from typing import Optional, Dict, Any


class DomainException(Exception):
    """Base exception for all domain-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ScrapingError(DomainException):
    """Raised when scraping operations fail."""
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.url = url
        self.status_code = status_code


class RateLimitError(ScrapingError):
    """Raised when rate limited by eBay."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class BotDetectionError(ScrapingError):
    """Raised when bot detection measures are triggered."""
    
    def __init__(
        self,
        message: str = "Bot detection triggered",
        captcha_detected: bool = False,
        security_measure_detected: bool = False,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.captcha_detected = captcha_detected
        self.security_measure_detected = security_measure_detected


class AuthenticationError(DomainException):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        auth_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.auth_type = auth_type


class ValidationError(DomainException):
    """Raised when data validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value


class ConfigurationError(DomainException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.config_key = config_key


class DataProcessingError(DomainException):
    """Raised when data processing operations fail."""
    
    def __init__(
        self,
        message: str,
        data_type: Optional[str] = None,
        processing_stage: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.data_type = data_type
        self.processing_stage = processing_stage


class NetworkError(ScrapingError):
    """Raised when network operations fail."""
    
    def __init__(
        self,
        message: str,
        timeout: Optional[float] = None,
        retry_count: int = 0,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.timeout = timeout
        self.retry_count = retry_count


class TerapeakError(ScrapingError):
    """Raised when Terapeak-specific operations fail."""
    
    def __init__(
        self,
        message: str,
        feature: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.feature = feature


class ProductNotFoundError(ScrapingError):
    """Raised when expected product data is not found."""
    
    def __init__(
        self,
        message: str = "Product not found",
        product_id: Optional[str] = None,
        search_criteria: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.product_id = product_id
        self.search_criteria = search_criteria


class ParsingError(DataProcessingError):
    """Raised when HTML/data parsing fails."""
    
    def __init__(
        self,
        message: str,
        selector: Optional[str] = None,
        html_snippet: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.selector = selector
        self.html_snippet = html_snippet[:200] if html_snippet else None  # Truncate for logging 