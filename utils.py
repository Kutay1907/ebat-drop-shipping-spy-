"""
Utility functions for the dropshipping analysis tool.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import asyncio
from fake_useragent import UserAgent


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('dropshipping_tool.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def clean_price_string(price_str: str) -> Optional[float]:
    """
    Extract numeric price from a price string.
    
    Args:
        price_str: Raw price string (e.g., "$19.99", "£25.50")
    
    Returns:
        Cleaned price as float or None if invalid
    """
    if not price_str:
        return None
    
    # Remove currency symbols and extract numbers
    price_clean = re.sub(r'[^\d.,]', '', price_str)
    price_clean = price_clean.replace(',', '')
    
    try:
        return float(price_clean)
    except (ValueError, TypeError):
        return None


def clean_title(title: str) -> str:
    """
    Clean and normalize product title for better matching.
    
    Args:
        title: Raw product title
    
    Returns:
        Cleaned title
    """
    if not title:
        return ""
    
    # Remove extra whitespace and normalize
    title = ' '.join(title.split())
    
    # Remove common marketplace-specific terms
    remove_terms = [
        'Brand New', 'Free Shipping', 'Fast Delivery', 'Ships Free',
        'New with Tags', 'NWT', 'NIB', 'New in Box'
    ]
    
    for term in remove_terms:
        title = re.sub(re.escape(term), '', title, flags=re.IGNORECASE)
    
    return title.strip()


def extract_sold_count(sold_text: str) -> int:
    """
    Extract sold count from eBay sold text.
    
    Args:
        sold_text: Text like "25 sold" or "100+ sold"
    
    Returns:
        Sold count as integer
    """
    if not sold_text:
        return 0
    
    # Extract numbers from sold text
    numbers = re.findall(r'\d+', sold_text)
    if numbers:
        return int(numbers[0])
    return 0


def calculate_profit_margin(ebay_price: float, amazon_price: float) -> float:
    """
    Calculate profit margin percentage.
    
    Args:
        ebay_price: eBay selling price
        amazon_price: Amazon buying price
    
    Returns:
        Profit margin as percentage
    """
    if amazon_price <= 0:
        return 0.0
    
    return ((ebay_price - amazon_price) / amazon_price) * 100


def is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
    
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def get_random_user_agent() -> str:
    """
    Get a random user agent string.
    
    Returns:
        Random user agent string
    """
    ua = UserAgent()
    return ua.random


async def save_results_to_file(results: Dict[str, Any], filename: str) -> None:
    """
    Save results to a JSON file asynchronously.
    
    Args:
        results: Result dictionary
        filename: Output filename
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logging.info(f"Results saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving results to file: {e}")


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format price with currency symbol.
    
    Args:
        amount: Price amount
        currency: Currency code (USD, GBP, EUR)
    
    Returns:
        Formatted currency string
    """
    symbols = {
        "USD": "$",
        "GBP": "£",
        "EUR": "€"
    }
    
    symbol = symbols.get(currency, "$")
    return f"{symbol}{amount:.2f}"


class RateLimiter:
    """
    Simple rate limiter for API calls.
    """
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def wait_if_needed(self) -> None:
        """
        Wait if rate limit would be exceeded.
        """
        import time
        
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.time_window]
        
        # If we're at the limit, wait
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                # Update calls list after waiting
                now = time.time()
                self.calls = [call_time for call_time in self.calls 
                             if now - call_time < self.time_window]
        
        # Record this call
        self.calls.append(now) 