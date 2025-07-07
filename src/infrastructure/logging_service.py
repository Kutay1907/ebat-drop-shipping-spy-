"""
Structured Logging Service

Implements structured logging with JSON output and multiple handlers.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict
from pathlib import Path

from ..domain.interfaces import ILogger
from ..domain.models import BotDetectionEvent


class StructuredLogger(ILogger):
    """
    Structured logging service implementing JSON logging format.
    
    Features:
    - JSON structured output
    - Multiple handlers (file and console)
    - Configurable log levels
    - Context enrichment
    """
    
    def __init__(self, config):
        """
        Initialize the structured logger.
        
        Args:
            config: Logging configuration object
        """
        self.config = config
        self.logger = logging.getLogger("ebay_scraper")
        self.logger.setLevel(getattr(logging, config.level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_file_handler()
        self._setup_console_handler()
    
    def _setup_file_handler(self):
        """Setup file logging handler."""
        if not self.config.log_to_file:
            return
        
        # Ensure log directory exists
        log_path = Path(self.config.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            self.config.log_file_path,
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count
        )
        
        file_handler.setLevel(getattr(logging, self.config.level.upper()))
        file_handler.setFormatter(JsonFormatter(self.config))
        self.logger.addHandler(file_handler)
    
    def _setup_console_handler(self):
        """Setup console logging handler."""
        if not self.config.log_to_console:
            return
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.config.console_level.upper()))
        
        if self.config.format == "json":
            console_handler.setFormatter(JsonFormatter(self.config))
        else:
            console_handler.setFormatter(TextFormatter(self.config))
        
        self.logger.addHandler(console_handler)
    
    async def log_info(self, message: str, **kwargs) -> None:
        """Log informational message."""
        self._log(logging.INFO, message, **kwargs)
    
    async def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    async def log_error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    async def log_bot_detection(self, event: BotDetectionEvent) -> None:
        """Log bot detection event."""
        self._log(
            logging.WARNING,
            "Bot detection event",
            event_type=event.event_type,
            url=event.url,
            captcha_detected=event.captcha_detected,
            security_measure_detected=event.security_measure_detected,
            timestamp=event.timestamp.isoformat(),
            retry_count=event.retry_count
        )
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method."""
        extra = {
            'custom_fields': kwargs,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.logger.log(level, message, extra=extra)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {}
        
        if self.config.include_timestamp:
            log_entry['timestamp'] = getattr(record, 'timestamp', 
                                           datetime.utcnow().isoformat())
        
        if self.config.include_level:
            log_entry['level'] = record.levelname
        
        if self.config.include_module:
            log_entry['module'] = record.module
        
        if self.config.include_function:
            log_entry['function'] = record.funcName
        
        log_entry['message'] = record.getMessage()
        
        # Add custom fields
        custom_fields = getattr(record, 'custom_fields', None)
        if custom_fields:
            log_entry.update(custom_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Text formatter for human-readable console output."""
    
    def __init__(self, config):
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        super().__init__(format_string)
        self.config = config 