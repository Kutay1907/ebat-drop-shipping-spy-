"""
CAPTCHA Handler Service

Manages CAPTCHA detection and manual intervention workflows.
Provides a bridge between automated scraping and human intervention.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from playwright.async_api import Page

from ..domain.interfaces import ICaptchaHandlerService, ILogger
from ..domain.models import CaptchaEvent, CaptchaStatus
from ..domain.exceptions import ScrapingError


class CaptchaHandlerService(ICaptchaHandlerService):
    """
    Service for detecting and handling CAPTCHA challenges.
    
    Features:
    - Multiple CAPTCHA detection methods
    - Manual intervention workflow
    - Status tracking and timeout handling
    - Integration with web UI for manual solving
    """
    
    def __init__(self, logger: ILogger, default_timeout: int = 300):
        """
        Initialize CAPTCHA handler service.
        
        Args:
            logger: Logger instance for tracking operations
            default_timeout: Default timeout for manual CAPTCHA solving (seconds)
        """
        self.logger = logger
        self.default_timeout = default_timeout
        self._pending_captchas: Dict[str, CaptchaEvent] = {}
        self._solved_captchas: Set[str] = set()
        self._captcha_selectors = [
            # reCAPTCHA selectors
            'iframe[src*="recaptcha"]',
            '.g-recaptcha',
            '#recaptcha',
            '[data-testid="recaptcha"]',
            
            # hCaptcha selectors
            'iframe[src*="hcaptcha"]',
            '.h-captcha',
            '#hcaptcha',
            
            # Generic CAPTCHA selectors
            '.captcha',
            '#captcha',
            '[class*="captcha"]',
            '[id*="captcha"]',
            'img[src*="captcha"]',
            
            # eBay specific selectors
            '#captcha_challenge',
            '.captcha-challenge',
            '[data-testid="captcha"]',
            
            # Text-based indicators
            'text=Enter the characters you see',
            'text=Please verify you are human',
            'text=Security check',
            'text=I\'m not a robot'
        ]
    
    async def detect_captcha(self, page: Page) -> bool:
        """
        Detect if CAPTCHA is present on the page.
        
        Args:
            page: Playwright page instance
            
        Returns:
            True if CAPTCHA is detected
        """
        try:
            await self.logger.log_info("Checking for CAPTCHA presence")
            
            # Check each selector for CAPTCHA elements
            for selector in self._captcha_selectors:
                try:
                    element = await page.wait_for_selector(
                        selector,
                        timeout=2000,
                        state='visible'
                    )
                    
                    if element:
                        await self.logger.log_warning(
                            "CAPTCHA detected",
                            selector=selector,
                            page_url=page.url
                        )
                        return True
                        
                except:
                    # Selector not found, continue checking
                    continue
            
            # Additional checks for suspicious page behavior
            if await self._check_suspicious_patterns(page):
                return True
            
            await self.logger.log_info("No CAPTCHA detected")
            return False
            
        except Exception as e:
            await self.logger.log_error(
                "Error during CAPTCHA detection",
                error=str(e),
                page_url=page.url if page else "unknown"
            )
            return False
    
    async def _check_suspicious_patterns(self, page: Page) -> bool:
        """Check for suspicious patterns that might indicate CAPTCHA."""
        try:
            page_content = await page.content()
            page_url = page.url
            
            # Suspicious URL patterns
            suspicious_url_patterns = [
                'captcha',
                'security',
                'verify',
                'robot',
                'challenge'
            ]
            
            if any(pattern in page_url.lower() for pattern in suspicious_url_patterns):
                await self.logger.log_warning(
                    "Suspicious URL pattern detected",
                    url=page_url
                )
                return True
            
            # Suspicious content patterns
            suspicious_content_patterns = [
                'verify you are human',
                'security check',
                'unusual traffic',
                'automated queries',
                'suspicious activity'
            ]
            
            page_text = page_content.lower()
            for pattern in suspicious_content_patterns:
                if pattern in page_text:
                    await self.logger.log_warning(
                        "Suspicious content pattern detected",
                        pattern=pattern,
                        url=page_url
                    )
                    return True
            
            return False
            
        except Exception as e:
            await self.logger.log_error(
                "Error checking suspicious patterns",
                error=str(e)
            )
            return False
    
    async def handle_captcha_manual(self, page: Page, result_id: str) -> bool:
        """
        Handle CAPTCHA with manual intervention.
        
        Args:
            page: Playwright page instance
            result_id: Associated scraping result ID
            
        Returns:
            True if CAPTCHA was solved successfully
        """
        event_id = str(uuid.uuid4())
        
        # Determine CAPTCHA type
        captcha_type = await self._identify_captcha_type(page)
        
        # Create CAPTCHA event
        captcha_event = CaptchaEvent(
            event_id=event_id,
            result_id=result_id,
            captcha_type=captcha_type,
            status=CaptchaStatus.DETECTED,
            page_url=page.url,
            manual_intervention_required=True
        )
        
        # Store pending CAPTCHA
        self._pending_captchas[event_id] = captcha_event
        
        await self.logger.log_warning(
            "CAPTCHA requires manual intervention",
            event_id=event_id,
            result_id=result_id,
            captcha_type=captcha_type,
            page_url=page.url
        )
        
        # Wait for manual resolution
        success = await self.wait_for_manual_solve(event_id, self.default_timeout)
        
        if success:
            captcha_event.status = CaptchaStatus.SOLVED
            captcha_event.solved_at = datetime.utcnow()
            await self.logger.log_info(
                "CAPTCHA solved manually",
                event_id=event_id,
                result_id=result_id
            )
        else:
            captcha_event.status = CaptchaStatus.FAILED
            await self.logger.log_error(
                "CAPTCHA manual solving failed or timed out",
                event_id=event_id,
                result_id=result_id,
                timeout=self.default_timeout
            )
        
        # Clean up
        self._pending_captchas.pop(event_id, None)
        
        return success
    
    async def _identify_captcha_type(self, page: Page) -> str:
        """Identify the type of CAPTCHA present."""
        try:
            # Check for reCAPTCHA
            if await page.query_selector('iframe[src*="recaptcha"]'):
                return "reCAPTCHA"
            
            # Check for hCaptcha
            if await page.query_selector('iframe[src*="hcaptcha"]'):
                return "hCaptcha"
            
            # Check for image CAPTCHA
            if await page.query_selector('img[src*="captcha"]'):
                return "Image CAPTCHA"
            
            # Check for text CAPTCHA
            page_content = await page.content()
            if 'enter the characters' in page_content.lower():
                return "Text CAPTCHA"
            
            return "Unknown CAPTCHA"
            
        except Exception as e:
            await self.logger.log_error(
                "Error identifying CAPTCHA type",
                error=str(e)
            )
            return "Unknown CAPTCHA"
    
    async def wait_for_manual_solve(self, event_id: str, timeout: int = 300) -> bool:
        """
        Wait for user to manually solve CAPTCHA.
        
        Args:
            event_id: CAPTCHA event identifier
            timeout: Maximum wait time in seconds
            
        Returns:
            True if CAPTCHA was marked as solved within timeout
        """
        start_time = datetime.utcnow()
        timeout_time = start_time + timedelta(seconds=timeout)
        
        await self.logger.log_info(
            "Waiting for manual CAPTCHA solution",
            event_id=event_id,
            timeout_seconds=timeout
        )
        
        while datetime.utcnow() < timeout_time:
            # Check if CAPTCHA was marked as solved
            if event_id in self._solved_captchas:
                self._solved_captchas.remove(event_id)
                return True
            
            # Wait before checking again
            await asyncio.sleep(2)
        
        await self.logger.log_warning(
            "Manual CAPTCHA solution timed out",
            event_id=event_id,
            timeout_seconds=timeout
        )
        
        return False
    
    async def mark_captcha_solved(self, event_id: str) -> None:
        """
        Mark CAPTCHA as solved by user.
        
        Args:
            event_id: CAPTCHA event identifier
        """
        if event_id in self._pending_captchas:
            self._solved_captchas.add(event_id)
            await self.logger.log_info(
                "CAPTCHA marked as solved",
                event_id=event_id
            )
        else:
            await self.logger.log_warning(
                "Attempted to mark non-existent CAPTCHA as solved",
                event_id=event_id
            )
    
    def get_pending_captchas(self) -> Dict[str, CaptchaEvent]:
        """Get all pending CAPTCHA events."""
        return self._pending_captchas.copy()
    
    def get_captcha_event(self, event_id: str) -> Optional[CaptchaEvent]:
        """Get specific CAPTCHA event by ID."""
        return self._pending_captchas.get(event_id)
    
    async def cleanup_expired_captchas(self, max_age_minutes: int = 60) -> None:
        """Clean up expired CAPTCHA events."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        expired_events = [
            event_id for event_id, event in self._pending_captchas.items()
            if event.detected_at < cutoff_time
        ]
        
        for event_id in expired_events:
            self._pending_captchas.pop(event_id, None)
            self._solved_captchas.discard(event_id)
        
        if expired_events:
            await self.logger.log_info(
                "Cleaned up expired CAPTCHA events",
                expired_count=len(expired_events)
            )
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get CAPTCHA handling statistics."""
        return {
            'pending_captchas': len(self._pending_captchas),
            'total_solved': len(self._solved_captchas),
            'detection_methods': len(self._captcha_selectors),
            'default_timeout': self.default_timeout
        } 