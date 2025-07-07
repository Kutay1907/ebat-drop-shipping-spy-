"""
eBay Login Automation Service

Automated login to eBay with 2FA support and session cookie management.
Implements clean architecture with proper error handling.
"""

import asyncio
import json
import os
from typing import Optional, Dict, Any
from pathlib import Path
from playwright.async_api import async_playwright, Page, BrowserContext

from ..domain.interfaces import IEbayLoginService, ILogger
from ..domain.exceptions import ScrapingError, ValidationError


class EbayLoginService(IEbayLoginService):
    """
    Service for automated eBay login with 2FA support.
    
    Features:
    - Headless browser automation
    - 2FA detection and waiting
    - Session cookie persistence
    - Multi-marketplace support
    - Retry logic for failed logins
    """
    
    def __init__(
        self, 
        logger: ILogger,
        headless: bool = True,
        login_timeout: int = 60,
        twofa_timeout: int = 300
    ):
        """
        Initialize eBay login service.
        
        Args:
            logger: Logger instance for tracking operations
            headless: Whether to run browser in headless mode
            login_timeout: Timeout for login process (seconds)
            twofa_timeout: Timeout for 2FA process (seconds)
        """
        self.logger = logger
        self.headless = headless
        self.login_timeout = login_timeout
        self.twofa_timeout = twofa_timeout
        self.browser_context: Optional[BrowserContext] = None
        self.current_page: Optional[Page] = None
        self._playwright = None
        self._browser = None
    
    async def initialize(self) -> None:
        """Initialize browser automation."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins'
            ]
        )
        
        await self.logger.log_info(
            "eBay login service initialized",
            headless=self.headless,
            timeout=self.login_timeout
        )
    
    async def login(self, username: str, password: str, marketplace: str = "ebay.com") -> bool:
        """
        Perform headless login to eBay.
        
        Args:
            username: eBay username or email
            password: eBay password
            marketplace: eBay marketplace (e.g., ebay.com, ebay.co.uk)
            
        Returns:
            True if login successful, False otherwise
        """
        if not username or not password:
            raise ValidationError("Username and password are required for login")
        
        try:
            # Create new browser context
            self.browser_context = await self._browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.current_page = await self.browser_context.new_page()
            
            # Navigate to eBay sign-in page
            signin_url = f"https://signin.{marketplace}/ws/eBayISAPI.dll?SignIn"
            await self.current_page.goto(signin_url, wait_until='networkidle')
            
            await self.logger.log_info(
                "Navigated to eBay sign-in page",
                url=signin_url,
                marketplace=marketplace
            )
            
            # Fill in credentials
            await self._fill_login_form(username, password)
            
            # Submit form and wait for response
            await self.current_page.click('button[type="submit"], input[type="submit"]')
            await self.current_page.wait_for_load_state('networkidle')
            
            # Check if 2FA is required
            if await self._is_two_factor_required():
                await self.logger.log_info("2FA required, waiting for user intervention")
                success = await self.handle_two_factor_auth(self.current_page)
                if not success:
                    await self.logger.log_error("2FA authentication failed")
                    return False
            
            # Verify login success
            if await self.is_logged_in():
                await self.logger.log_info(
                    "Successfully logged into eBay",
                    username=username,
                    marketplace=marketplace
                )
                return True
            else:
                await self.logger.log_error(
                    "Login failed - credentials may be incorrect",
                    username=username,
                    marketplace=marketplace
                )
                return False
                
        except Exception as e:
            await self.logger.log_error(
                "eBay login failed with exception",
                error=str(e),
                username=username,
                marketplace=marketplace
            )
            raise ScrapingError(f"Login failed: {str(e)}")
    
    async def _fill_login_form(self, username: str, password: str) -> None:
        """Fill in the login form."""
        # Wait for form elements to be available
        await self.current_page.wait_for_selector('#userid', timeout=10000)
        
        # Fill username
        await self.current_page.fill('#userid', username)
        await asyncio.sleep(0.5)  # Human-like delay
        
        # Fill password
        await self.current_page.fill('#pass', password)
        await asyncio.sleep(0.5)
        
        await self.logger.log_info("Login form filled successfully")
    
    async def _is_two_factor_required(self) -> bool:
        """Check if 2FA is required."""
        # Common 2FA indicators on eBay
        twofa_selectors = [
            '[data-testid="2fa"]',
            '#twofa',
            '.two-factor',
            'input[name="otp"]',
            'input[name="verification_code"]',
            'text=verification code',
            'text=two-factor',
            'text=authenticator'
        ]
        
        for selector in twofa_selectors:
            try:
                element = await self.current_page.wait_for_selector(
                    selector, 
                    timeout=3000,
                    state='visible'
                )
                if element:
                    return True
            except:
                continue
        
        return False
    
    async def handle_two_factor_auth(self, page: Page) -> bool:
        """
        Handle 2FA authentication.
        
        This method waits for the user to manually complete 2FA
        or detects when 2FA is completed automatically.
        
        Args:
            page: Playwright page instance
            
        Returns:
            True if 2FA completed successfully
        """
        await self.logger.log_info(
            "2FA detected - waiting for completion",
            timeout=self.twofa_timeout
        )
        
        # In headless mode, we need to wait for 2FA to be completed
        # This could be done by:
        # 1. Switching to non-headless temporarily
        # 2. Using SMS/email code input
        # 3. Waiting for navigation away from 2FA page
        
        try:
            # Wait for navigation away from 2FA page (indicates completion)
            await page.wait_for_url(
                lambda url: '2fa' not in url.lower() and 'signin' not in url.lower(),
                timeout=self.twofa_timeout * 1000
            )
            
            await self.logger.log_info("2FA completed successfully")
            return True
            
        except Exception as e:
            await self.logger.log_warning(
                "2FA timeout or failed",
                error=str(e),
                timeout=self.twofa_timeout
            )
            return False
    
    async def is_logged_in(self) -> bool:
        """Check if current session is authenticated."""
        if not self.current_page:
            return False
        
        try:
            # Check for logged-in indicators
            logged_in_selectors = [
                '#gh-ug',  # User greeting
                '.account-info',
                '[data-testid="user-menu"]',
                'text=My eBay',
                'text=Sign out'
            ]
            
            for selector in logged_in_selectors:
                try:
                    element = await self.current_page.wait_for_selector(
                        selector,
                        timeout=5000,
                        state='visible'
                    )
                    if element:
                        return True
                except:
                    continue
            
            # Check current URL for logged-in patterns
            current_url = self.current_page.url
            if any(pattern in current_url for pattern in ['/myb/', '/mys/', '/usr/']):
                return True
            
            return False
            
        except Exception as e:
            await self.logger.log_error(
                "Failed to check login status",
                error=str(e)
            )
            return False
    
    async def export_session_cookies(self, file_path: str) -> None:
        """Export session cookies to JSON file."""
        if not self.browser_context:
            raise ScrapingError("No active browser context to export cookies from")
        
        try:
            # Get all cookies from the browser context
            cookies = await self.browser_context.cookies()
            
            # Filter eBay-related cookies
            ebay_cookies = [
                cookie for cookie in cookies 
                if 'ebay' in cookie.get('domain', '').lower()
            ]
            
            # Create session state object
            session_state = {
                'cookies': ebay_cookies,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'timestamp': asyncio.get_event_loop().time(),
                'logged_in': await self.is_logged_in()
            }
            
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(session_state, f, indent=2, default=str)
            
            await self.logger.log_info(
                "Session cookies exported successfully",
                file_path=file_path,
                cookies_count=len(ebay_cookies)
            )
            
        except Exception as e:
            await self.logger.log_error(
                "Failed to export session cookies",
                error=str(e),
                file_path=file_path
            )
            raise ScrapingError(f"Cookie export failed: {str(e)}")
    
    async def load_session_cookies(self, file_path: str) -> bool:
        """Load session cookies from JSON file."""
        if not os.path.exists(file_path):
            await self.logger.log_warning(
                "Session cookies file not found",
                file_path=file_path
            )
            return False
        
        try:
            with open(file_path, 'r') as f:
                session_state = json.load(f)
            
            if not self.browser_context:
                await self.logger.log_error("No browser context available for loading cookies")
                return False
            
            # Add cookies to browser context
            await self.browser_context.add_cookies(session_state['cookies'])
            
            await self.logger.log_info(
                "Session cookies loaded successfully",
                file_path=file_path,
                cookies_count=len(session_state['cookies'])
            )
            
            return True
            
        except Exception as e:
            await self.logger.log_error(
                "Failed to load session cookies",
                error=str(e),
                file_path=file_path
            )
            return False
    
    async def refresh_session(self) -> bool:
        """Refresh existing session or re-login if needed."""
        if await self.is_logged_in():
            await self.logger.log_info("Session is still valid, no refresh needed")
            return True
        
        await self.logger.log_info("Session expired, attempting to refresh")
        
        # Try to load stored session first
        if await self.load_session_cookies('ebay_state.json'):
            if await self.is_logged_in():
                await self.logger.log_info("Session refreshed from stored cookies")
                return True
        
        # If stored session doesn't work, need fresh login
        await self.logger.log_warning("Stored session invalid, manual re-login required")
        return False
    
    async def cleanup(self) -> None:
        """Cleanup browser resources."""
        try:
            if self.current_page:
                await self.current_page.close()
            
            if self.browser_context:
                await self.browser_context.close()
            
            if self._browser:
                await self._browser.close()
            
            if self._playwright:
                await self._playwright.stop()
            
            await self.logger.log_info("eBay login service cleanup completed")
            
        except Exception as e:
            await self.logger.log_error(
                "Error during login service cleanup",
                error=str(e)
            ) 