"""
Retry Handler Service

Provides retry logic with exponential backoff for failed operations.
"""

import asyncio
import random
from typing import Callable, Any, Optional

from ..domain.interfaces import IRetryHandler


class RetryHandler(IRetryHandler):
    """
    Service for handling retries with exponential backoff.
    
    Features:
    - Configurable retry attempts
    - Exponential backoff with jitter
    - Exception-specific handling
    """
    
    def __init__(self, config):
        """
        Initialize with retry configuration.
        
        Args:
            config: Retry configuration object
        """
        self.config = config
        self.max_retries = config.max_retries
        self.base_backoff = config.base_backoff
        self.max_backoff = config.max_backoff
        self.backoff_factor = config.backoff_factor
    
    async def execute_with_retry(
        self,
        operation: Callable,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None
    ) -> Any:
        """
        Execute operation with retry logic.
        
        Args:
            operation: Async callable to execute
            max_retries: Maximum number of retries (overrides config)
            backoff_factor: Exponential backoff factor (overrides config)
            
        Returns:
            Operation result
            
        Raises:
            Last exception if all retries fail
        """
        effective_max_retries = max_retries if max_retries is not None else self.max_retries
        effective_backoff_factor = backoff_factor if backoff_factor is not None else self.backoff_factor
        
        last_exception: Optional[Exception] = None
        
        for attempt in range(effective_max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                last_exception = e
                
                if attempt == effective_max_retries:
                    # Final attempt failed
                    break
                
                # Calculate backoff time
                backoff_time = min(
                    self.base_backoff * (effective_backoff_factor ** attempt),
                    self.max_backoff
                )
                
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0.1, 0.3) * backoff_time
                total_delay = backoff_time + jitter
                
                await asyncio.sleep(total_delay)
        
        # All retries failed, raise the last exception
        if last_exception is not None:
            raise last_exception
        else:
            raise RuntimeError("Operation failed without exception") 