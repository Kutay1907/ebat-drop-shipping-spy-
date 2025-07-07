"""
Bot Protection Service

Comprehensive bot detection avoidance and protection measures.
Implements sophisticated anti-detection strategies for eBay scraping.
"""

import asyncio
import random
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from ..domain.interfaces import IBotProtection, ILogger, IUserAgentRotator
from ..domain.models import BotDetectionEvent
from ..domain.exceptions import BotDetectionError, RateLimitError


class BotProtectionService(IBotProtection):
    """
    Advanced bot protection service implementing multiple anti-detection strategies.
    
    Features:
    - Human-like interaction patterns
    - CAPTCHA detection
    - Rate limiting detection
    - Dynamic delays with jitter
    - Mouse movement simulation
    - Scroll behavior simulation
    - User agent rotation
    """
    
    def __init__(
        self,
        user_agent_rotator: IUserAgentRotator,
        logger: ILogger,
        min_delay: float = 1.0,
        max_delay: float = 5.0,
        scroll_probability: float = 0.7,
        mouse_move_probability: float = 0.8
    ):
        """
        Initialize bot protection service.
        
        Args:
            user_agent_rotator: Service for rotating user agents
            logger: Logging service
            min_delay: Minimum delay between actions (seconds)
            max_delay: Maximum delay between actions (seconds)
            scroll_probability: Probability of scrolling during page interaction
            mouse_move_probability: Probability of mouse movement during page interaction
        """
        self._user_agent_rotator = user_agent_rotator
        self._logger = logger
        self._min_delay = min_delay
        self._max_delay = max_delay
        self._scroll_probability = scroll_probability
        self._mouse_move_probability = mouse_move_probability
        
        # Track interaction patterns
        self._last_action_time = datetime.utcnow()
        self._action_count = 0
        self._session_start_time = datetime.utcnow()

    async def apply_protection(self, page: Page) -> None:
        """
        Apply comprehensive bot protection measures to a page.
        
        Args:
            page: Playwright page instance
        """
        await self._logger.log_info("Applying bot protection measures")
        
        # Set random user agent
        await self._set_user_agent(page)
        
        # Apply stealth measures
        await self._apply_stealth_measures(page)
        
        # Simulate human-like timing
        await self._apply_human_timing()
        
        # Random mouse movements
        if random.random() < self._mouse_move_probability:
            await self._simulate_mouse_movement(page)
        
        # Random scrolling
        if random.random() < self._scroll_probability:
            await self._simulate_scrolling(page)
        
        # Check for bot detection after actions
        await self._check_bot_detection(page)

    async def handle_detection(self, page: Page, event: BotDetectionEvent) -> bool:
        """
        Handle detected bot protection measures.
        
        Args:
            page: Playwright page instance
            event: Bot detection event details
            
        Returns:
            True if successfully handled, False otherwise
        """
        await self._logger.log_bot_detection(event)
        
        if event.captcha_detected:
            return await self._handle_captcha(page, event)
        elif event.security_measure_detected:
            return await self._handle_security_measure(page, event)
        else:
            return await self._handle_generic_detection(page, event)

    async def is_rate_limited(self, page: Page) -> bool:
        """
        Check if current page indicates rate limiting.
        
        Args:
            page: Playwright page instance
            
        Returns:
            True if rate limited
        """
        try:
            # Check for common rate limiting indicators
            rate_limit_selectors = [
                "text='Security Measure'",
                "text='unusual traffic'",
                "text='temporarily blocked'",
                "text='try again later'",
                "[aria-label*='security']",
                ".captcha",
                "#captcha",
                "text='robot'",
                "text='automated'",
                "text='blocked'"
            ]
            
            for selector in rate_limit_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=1000)
                    if element:
                        await self._logger.log_warning(
                            "Rate limiting detected",
                            selector=selector,
                            url=page.url
                        )
                        return True
                except PlaywrightTimeoutError:
                    continue
            
            # Check HTTP status codes that might indicate rate limiting
            response = page.url
            if "error" in response.lower() or "block" in response.lower():
                return True
            
            return False
            
        except Exception as e:
            await self._logger.log_error(
                "Error checking rate limit status",
                error=str(e),
                url=page.url
            )
            return False

    async def _set_user_agent(self, page: Page) -> None:
        """Set a random user agent for the page."""
        try:
            user_agent = self._user_agent_rotator.get_random_user_agent()
            await page.set_extra_http_headers({
                'User-Agent': user_agent
            })
            await self._logger.log_info("User agent set", user_agent=user_agent[:50])
        except Exception as e:
            await self._logger.log_error("Failed to set user agent", error=str(e))

    async def _apply_stealth_measures(self, page: Page) -> None:
        """Apply JavaScript-based stealth measures."""
        try:
            # Remove webdriver property
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            # Modify chrome object
            await page.add_init_script("""
                window.chrome = {
                    runtime: {},
                };
            """)
            
            # Modify permissions query
            await page.add_init_script("""
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
        except Exception as e:
            await self._logger.log_error("Failed to apply stealth measures", error=str(e))

    async def _apply_human_timing(self) -> None:
        """Apply human-like timing between actions."""
        current_time = datetime.utcnow()
        time_since_last_action = (current_time - self._last_action_time).total_seconds()
        
        # Calculate adaptive delay based on action frequency
        base_delay = random.uniform(self._min_delay, self._max_delay)
        
        # Add jitter based on time patterns
        if time_since_last_action < 1.0:
            # If actions are too frequent, add extra delay
            base_delay += random.uniform(1.0, 3.0)
        
        # Session-based slowdown
        session_duration = (current_time - self._session_start_time).total_seconds()
        if session_duration > 300:  # After 5 minutes, slow down
            base_delay *= 1.5
        
        await asyncio.sleep(base_delay)
        
        self._last_action_time = current_time
        self._action_count += 1

    async def _simulate_mouse_movement(self, page: Page) -> None:
        """Simulate realistic mouse movements."""
        try:
            # Get viewport size
            viewport = page.viewport_size or {"width": 1280, "height": 720}
            
            # Generate random mouse movements
            movements = random.randint(2, 5)
            for _ in range(movements):
                x = random.randint(100, viewport["width"] - 100)
                y = random.randint(100, viewport["height"] - 100)
                
                await page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
        except Exception as e:
            await self._logger.log_error("Failed to simulate mouse movement", error=str(e))

    async def _simulate_scrolling(self, page: Page) -> None:
        """Simulate human-like scrolling behavior."""
        try:
            # Random scroll patterns
            scroll_patterns = [
                # Slow continuous scroll
                lambda: self._smooth_scroll(page, random.randint(200, 800), 0.1),
                # Quick scroll down and back up
                lambda: self._quick_scroll_pattern(page),
                # Multiple small scrolls
                lambda: self._small_scroll_pattern(page)
            ]
            
            pattern = random.choice(scroll_patterns)
            await pattern()
            
        except Exception as e:
            await self._logger.log_error("Failed to simulate scrolling", error=str(e))

    async def _smooth_scroll(self, page: Page, distance: int, delay: float) -> None:
        """Perform smooth scrolling."""
        steps = random.randint(5, 15)
        step_size = distance // steps
        
        for _ in range(steps):
            await page.mouse.wheel(0, step_size)
            await asyncio.sleep(delay)

    async def _quick_scroll_pattern(self, page: Page) -> None:
        """Perform quick scroll down and back up."""
        # Scroll down
        await page.mouse.wheel(0, random.randint(500, 1000))
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Scroll back up
        await page.mouse.wheel(0, -random.randint(300, 600))
        await asyncio.sleep(random.uniform(0.3, 0.8))

    async def _small_scroll_pattern(self, page: Page) -> None:
        """Perform multiple small scrolls."""
        scrolls = random.randint(3, 7)
        for _ in range(scrolls):
            await page.mouse.wheel(0, random.randint(100, 300))
            await asyncio.sleep(random.uniform(0.2, 0.5))

    async def _check_bot_detection(self, page: Page) -> None:
        """Check for signs of bot detection."""
        try:
            # Check for CAPTCHA
            captcha_selectors = [
                ".captcha",
                "#captcha", 
                "[data-testid*='captcha']",
                "iframe[src*='captcha']",
                "text='prove you are human'"
            ]
            
            for selector in captcha_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=500)
                    if element:
                        event = BotDetectionEvent(
                            event_type="captcha_detected",
                            url=page.url,
                            captcha_detected=True
                        )
                        raise BotDetectionError("CAPTCHA detected", captcha_detected=True)
                except PlaywrightTimeoutError:
                    continue
            
            # Check for security measures
            security_selectors = [
                "text='Security Measure'",
                "text='suspicious activity'",
                "text='automated traffic'",
                "text='unusual behavior'"
            ]
            
            for selector in security_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=500)
                    if element:
                        event = BotDetectionEvent(
                            event_type="security_measure_detected",
                            url=page.url,
                            security_measure_detected=True
                        )
                        raise BotDetectionError(
                            "Security measure detected",
                            security_measure_detected=True
                        )
                except PlaywrightTimeoutError:
                    continue
                    
        except BotDetectionError:
            raise
        except Exception as e:
            await self._logger.log_error("Error checking bot detection", error=str(e))

    async def _handle_captcha(self, page: Page, event: BotDetectionEvent) -> bool:
        """Handle CAPTCHA detection."""
        await self._logger.log_warning(
            "CAPTCHA detected - manual intervention required",
            url=page.url
        )
        
        # In a production system, this could:
        # 1. Notify administrators
        # 2. Pause automation
        # 3. Switch to different proxy/session
        # 4. Implement CAPTCHA solving service
        
        return False  # Cannot automatically handle CAPTCHA

    async def _handle_security_measure(self, page: Page, event: BotDetectionEvent) -> bool:
        """Handle security measure detection."""
        await self._logger.log_warning(
            "Security measure detected - implementing countermeasures",
            url=page.url
        )
        
        # Wait longer before retrying
        await asyncio.sleep(random.uniform(30, 60))
        
        # Clear cookies and restart session
        await page.context.clear_cookies()
        
        return True  # Indicate that countermeasures were applied

    async def _handle_generic_detection(self, page: Page, event: BotDetectionEvent) -> bool:
        """Handle generic bot detection."""
        await self._logger.log_warning(
            "Generic bot detection - applying standard countermeasures",
            url=page.url
        )
        
        # Apply longer delay
        await asyncio.sleep(random.uniform(10, 30))
        
        # Simulate more human behavior
        await self._simulate_mouse_movement(page)
        await self._simulate_scrolling(page)
        
        return True 