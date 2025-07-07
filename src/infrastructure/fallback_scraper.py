"""
Real Fallback Scraper Service

Production implementation for eBay product scraping.
Uses Playwright for web automation when Terapeak is unavailable.
"""

import asyncio
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from urllib.parse import urlencode, quote_plus

from ..domain.interfaces import IProductScraper, ILogger, IBotProtection
from ..domain.models import (
    SearchCriteria, 
    Product,
    ProductCondition
)
from ..domain.exceptions import (
    ScrapingError,
    BotDetectionError,
    RateLimitError,
    ProductNotFoundError
)


class FallbackScraper(IProductScraper):
    """
    Real fallback scraper for eBay product data.
    
    This service scrapes public eBay search results when Terapeak is unavailable
    or authentication fails. Uses robust selectors and error handling.
    """
    
    def __init__(
        self,
        bot_protection: IBotProtection,
        logger: ILogger,
        headless: bool = True,
        timeout: float = 30.0
    ):
        """
        Initialize fallback scraper.
        
        Args:
            bot_protection: Bot protection service
            logger: Logging service
            headless: Whether to run browser in headless mode
            timeout: Request timeout in seconds
        """
        self.bot_protection = bot_protection
        self.logger = logger
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
    
    async def scrape_products(self, criteria: SearchCriteria) -> List[Product]:
        """
        Scrape products based on search criteria from eBay search results.
        
        Args:
            criteria: Search parameters and filters
            
        Returns:
            List of scraped products
            
        Raises:
            ScrapingError: When scraping fails
            BotDetectionError: When bot detection is triggered
            RateLimitError: When rate limited by eBay
        """
        await self.logger.log_info(
            "Starting fallback eBay scraping",
            keyword=criteria.keyword,
            max_results=criteria.max_results,
            marketplace=criteria.marketplace
        )
        
        page = None
        products = []
        
        try:
            # ✅ CRITICAL FIX: Ensure browser is properly initialized for each scraping session
            await self._ensure_browser_ready()
            
            # Ensure context is ready before creating page
            if not self.context:
                raise ScrapingError("Browser context not available")
            
            # Create new page for scraping
            page = await self.context.new_page()
            
            # ✅ Set up page event handlers to catch browser issues early
            search_keyword = criteria.keyword  # Capture keyword for lambda scope
            page.on("crash", lambda: asyncio.create_task(self.logger.log_error(f"❌ Page crashed during scraping for '{search_keyword}'")))
            page.on("close", lambda: asyncio.create_task(self.logger.log_warning(f"⚠️ Page closed during scraping for '{search_keyword}'")))
            
            # Apply bot protection before navigating
                await self.bot_protection.apply_protection(page)
                
                # Build search URL
                search_url = self._build_search_url(criteria)
            
                await self.logger.log_info(
                    "Navigating to eBay search",
                    url=search_url
                )
                
            # ✅ Enhanced navigation with better error handling
            try:
                await page.goto(search_url, wait_until='networkidle', timeout=self.timeout * 1000)
            except Exception as nav_error:
                await self.logger.log_error(
                    "❌ Failed to navigate to eBay search page",
                    url=search_url,
                    error=str(nav_error)
                )
                raise ScrapingError(f"Navigation failed: {str(nav_error)}", url=search_url)
            
            # ✅ Check if browser/page is still alive after navigation
            if page.is_closed():
                raise ScrapingError("Browser page closed unexpectedly after navigation", url=search_url)
            
            # Check for rate limiting or blocking
            await self._check_rate_limit_status(page, search_url)
                
                # Wait for search results to load
                await self._wait_for_search_results(page)
                
            # ✅ Double-check browser state before extraction
            if page.is_closed():
                raise ScrapingError("Browser page closed unexpectedly before extraction", keyword=criteria.keyword)
            
            # Extract products from search results
            products = await self._extract_products_from_search(page, criteria.max_results)
                
                await self.logger.log_info(
                    "Fallback scraping completed successfully",
                    keyword=criteria.keyword,
                    products_found=len(products)
                )
                
        except BotDetectionError:
            # Re-raise bot detection errors
            raise
        except RateLimitError:
            # Re-raise rate limit errors
            raise
        except Exception as e:
            await self.logger.log_error(
                "Failed to extract products from search results",
                keyword=criteria.keyword,
                error=str(e)
            )
            # Don't raise here, return empty list as fallback
            products = []
        
        finally:
            # ✅ CRITICAL FIX: Proper cleanup with error handling
            if page and not page.is_closed():
                try:
                    await page.close()
                    await self.logger.log_info("✅ Page cleanup completed successfully")
                except Exception as cleanup_error:
                    await self.logger.log_warning(
                        "⚠️ Page cleanup failed",
                        error=str(cleanup_error)
                    )
        
        return products
    
    async def _ensure_browser_ready(self) -> None:
        """Ensure browser and context are ready for scraping with enhanced stealth checks."""
        try:
            # Check if browser exists and is connected
            if not self.browser or not self.browser.is_connected():
                await self.logger.log_info("🔄 Initializing new stealth browser session")
                await self._initialize_browser()
            
            # Ensure we have a valid browser after initialization
            if not self.browser:
                raise ScrapingError("Failed to initialize browser")
            
            # Check if context exists and is valid
            if not self.context:
                await self.logger.log_info("🔄 Creating fresh stealth browser context")
                
                self.context = await self.browser.new_context(
                    viewport={"width": 1366, "height": 768},
                    user_agent=self._get_stealth_user_agent(),
                    locale="en-US",
                    timezone_id="America/New_York",
                    permissions=["geolocation"],
                    geolocation={"latitude": 40.7128, "longitude": -74.0060},
                    screen={"width": 1920, "height": 1080},
                    color_scheme="light",
                    device_scale_factor=1,
                    java_script_enabled=True,
                    extra_http_headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Cache-Control": "max-age=0",
                        "DNT": "1",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": '"Windows"',
                    }
                )
                
                # ✅ INJECT STEALTH SCRIPTS: Prevent detection after context creation
                await self._inject_stealth_scripts()
                
                await self.logger.log_info("✅ Created fresh stealth browser context with anti-detection measures")
                
        except Exception as e:
            await self.logger.log_error(
                "❌ Failed to ensure browser readiness",
                error=str(e)
            )
            raise ScrapingError(f"Browser initialization failed: {str(e)}")
    
    async def _initialize_browser(self):
        """Initialize maximum stealth browser with all advanced anti-detection techniques."""
        # ✅ ULTIMATE STEALTH ARGS: Based on latest research for eBay bypassing
        stealth_args = [
            # ✅ CORE ANTI-DETECTION: Disable automation signatures
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--exclude-switches=enable-automation",
            "--disable-dev-shm-usage",
            
            # ✅ REMOVE AUTOMATION TRACES
            "--disable-extensions",
            "--disable-plugins",
            "--disable-default-apps",
            "--disable-infobars",
            "--disable-web-security",
            
            # ✅ PERFORMANCE STEALTH: Look like real browser
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-features=TranslateUI",
            "--disable-features=VizDisplayCompositor",
            "--disable-ipc-flooding-protection",
            
            # ✅ NETWORK STEALTH
            "--disable-background-networking",
            "--disable-sync",
            "--disable-translate",
            "--no-first-run",
            "--no-default-browser-check",
            
            # ✅ VISUAL STEALTH
            "--disable-gpu",
            "--hide-scrollbars",
            "--mute-audio",
            "--window-size=1366,768",
            "--start-maximized",
            
            # ✅ PRIVACY STEALTH
            "--disable-logging",
            "--disable-login-animations",
            "--disable-notifications",
            "--disable-password-generation",
            "--disable-save-password-bubble",
            "--disable-single-click-autofill",
            "--no-pings",
            "--no-zygote",
            "--disable-background-mode",
            "--disable-add-to-shelf",
            "--disable-client-side-phishing-detection",
            "--disable-datasaver-prompt",
            "--disable-domain-reliability",
            
            # ✅ ADVANCED STEALTH: Additional measures
            "--disable-extensions-file-access-check",
            "--disable-extensions-http-throttling",
            "--disable-component-extensions-with-background-pages",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-device-discovery-notifications",
        ]
        
        try:
            # ✅ STANDARD PLAYWRIGHT WITH MAXIMUM STEALTH
            from playwright.async_api import async_playwright
            playwright = await async_playwright().start()
            
            # ✅ STEALTH BROWSER: Maximum stealth configuration
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=stealth_args,
                slow_mo=200,  # More human-like timing
                devtools=False,
            )
            
            # ✅ ULTIMATE STEALTH CONTEXT: Maximum human-like behavior
            self.context = await self.browser.new_context(
                # ✅ REALISTIC VIEWPORT
                viewport={"width": 1366, "height": 768},
                
                # ✅ ROTATING REALISTIC USER AGENTS
                user_agent=self._get_advanced_stealth_user_agent(),
                
                # ✅ HUMAN LOCALE AND TIMEZONE
                locale="en-US",
                timezone_id="America/New_York",
                
                # ✅ REALISTIC PERMISSIONS
                permissions=["geolocation", "notifications"],
                geolocation={"latitude": 40.7128, "longitude": -74.0060},
                
                # ✅ REALISTIC SCREEN PROPERTIES
                screen={"width": 1920, "height": 1080},
                color_scheme="light",
                device_scale_factor=1,
                
                # ✅ ENABLE JAVASCRIPT FOR NORMAL BEHAVIOR
                java_script_enabled=True,
                
                # ✅ REALISTIC HTTP HEADERS
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cache-Control": "max-age=0",
                    "DNT": "1",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-ch-ua-arch": '"x86"',
                    "sec-ch-ua-bitness": '"64"',
                    "sec-ch-ua-full-version": '"120.0.6099.109"',
                    "sec-ch-ua-platform-version": '"10.0.0"',
                }
            )
            
            # ✅ INJECT ULTIMATE STEALTH SCRIPTS
            await self._inject_ultimate_stealth_scripts()
            await self.logger.log_info("✅ Maximum stealth browser initialized successfully")
            
        except Exception as e:
            await self.logger.log_error(f"Failed to initialize stealth browser: {str(e)}")
            raise ScrapingError(
                f"Browser initialization failed: {str(e)}",
                details={"browser_type": "stealth_failed"}
            )
    
    def _get_advanced_stealth_user_agent(self) -> str:
        """Get the most realistic user agent string optimized for undetected-playwright."""
        import random
        
        # ✅ LATEST USER AGENTS: Recently collected from real browsers (Dec 2024)
        ultra_realistic_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        return random.choice(ultra_realistic_agents)
    
    async def _inject_ultimate_stealth_scripts(self) -> None:
        """Inject the most advanced stealth JavaScript to prevent all forms of detection."""
        if not self.context:
            return
            
        ultimate_stealth_script = """
        // ✅ ULTIMATE STEALTH: Remove all automation indicators
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        
        // ✅ ADVANCED: Override chrome detection
        Object.defineProperty(window, 'chrome', {
            get: () => ({
                runtime: {
                    onConnect: undefined,
                    onMessage: undefined,
                },
                loadTimes: () => ({}),
                csi: () => ({}),
                app: {}
            }),
        });
        
        // ✅ STEALTH: Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // ✅ ULTIMATE: Override plugin detection
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format", 
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                }
            ],
        });
        
        // ✅ STEALTH: Override languages  
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // ✅ ULTIMATE CDP PROTECTION: Override console methods to prevent Runtime.enable detection
        const methods = ['debug', 'error', 'info', 'log', 'warn', 'dir', 'dirxml', 'table', 'trace', 'group', 'groupCollapsed', 'groupEnd', 'clear', 'count', 'countReset', 'assert', 'profile', 'profileEnd', 'time', 'timeLog', 'timeEnd', 'timeStamp'];
        
        methods.forEach(method => {
            const original = console[method];
            console[method] = function() {
                // Silently ignore console calls to prevent CDP detection
                return undefined;
            };
        });
        
        // ✅ ADVANCED: Override timing functions for human-like behavior
        const originalSetTimeout = window.setTimeout;
        window.setTimeout = function(fn, delay, ...args) {
            // Add slight randomness to timeouts
            const randomDelay = delay + Math.random() * 50;
            return originalSetTimeout(fn, randomDelay, ...args);
        };
        
        // ✅ STEALTH: Override screen properties
        Object.defineProperty(screen, 'colorDepth', {
            get: () => 24,
        });
        
        Object.defineProperty(screen, 'pixelDepth', {
            get: () => 24,
        });
        
        // ✅ ULTIMATE: Hide automation traces
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """
        
        try:
            await self.context.add_init_script(ultimate_stealth_script)
            await self.logger.log_info("✅ Ultimate stealth scripts injected successfully")
        except Exception as e:
            await self.logger.log_warning(
                "⚠️ Failed to inject ultimate stealth scripts",
                error=str(e)
            )
    
    def _get_stealth_user_agent(self) -> str:
        """Get a realistic user agent string that rotates to avoid detection."""
        import random
        
        # ✅ REAL USER AGENTS: Recently collected from actual browsers
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        return random.choice(user_agents)
    
    async def _inject_stealth_scripts(self) -> None:
        """Inject stealth JavaScript to prevent detection."""
        if not self.context:
            await self.logger.log_warning("⚠️ Cannot inject stealth scripts: no browser context")
            return
            
        stealth_script = """
        // ✅ STEALTH: Remove automation indicators
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        
        // ✅ STEALTH: Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // ✅ STEALTH: Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // ✅ STEALTH: Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // ✅ STEALTH: Chrome runtime fix
        if (!window.chrome) {
            window.chrome = {};
        }
        if (!window.chrome.runtime) {
            window.chrome.runtime = {};
        }
        
        // ✅ STEALTH: Console modifications to prevent CDP detection
        const consoleDebug = console.debug;
        const consoleError = console.error;
        const consoleInfo = console.info;
        const consoleLog = console.log;
        const consoleWarn = console.warn;
        
        // Override console methods that might trigger CDP detection
        console.debug = function() {};
        console.clear = function() {};
        console.log = function() {};
        console.info = function() {};
        console.error = function() {};
        console.warn = function() {};
        """
        
        try:
            await self.context.add_init_script(stealth_script)
            await self.logger.log_info("✅ Stealth scripts injected successfully")
        except Exception as e:
            await self.logger.log_warning(
                "⚠️ Failed to inject stealth scripts",
                error=str(e)
            )
    
    def _build_search_url(self, criteria: SearchCriteria) -> str:
        """Build eBay search URL with all criteria."""
        base_url = "https://www.ebay.com/sch/i.html"
        
        params = {
            "_nkw": criteria.keyword,
            "_sacat": "0",  # All categories
            "_sop": "12",   # Sort by ending soon
        }
        
        # Add price filters
        if criteria.min_price:
            params["_udlo"] = str(criteria.min_price)
        if criteria.max_price:
            params["_udhi"] = str(criteria.max_price)
        
        # Add condition filter
        if criteria.condition and criteria.condition != "ANY":
            condition_map = {
                "NEW": "1000",
                "USED": "3000", 
                "REFURBISHED": "2000"
            }
            if criteria.condition.upper() in condition_map:
                params["LH_ItemCondition"] = condition_map[criteria.condition.upper()]
        
        # Add sold listings filter if requested
        if criteria.sold_listings_only:
            params["LH_Sold"] = "1"
            params["LH_Complete"] = "1"
        
        # Add free shipping filter
        if criteria.free_shipping_only:
            params["LH_FS"] = "1"
        
        return f"{base_url}?{urlencode(params)}"
    
    async def _check_rate_limit_status(self, page, url: str) -> None:
        """Check if we're being rate limited or blocked."""
        try:
            # ✅ Check if page is still alive before checking content
            if page.is_closed():
                raise ScrapingError("Page closed before rate limit check", url=url)
                
            # Check page title and content for rate limiting indicators
            title = await page.title()
            if any(indicator in title.lower() for indicator in ['blocked', 'security', 'verify', 'captcha']):
                await self.logger.log_warning(
                    "Potential rate limiting detected",
                    title=title,
                    url=url
                )
                raise RateLimitError(f"Rate limiting detected: {title}")
                
        except Exception as e:
            # ✅ Enhanced error logging for rate limit checks
            await self.logger.log_error(
                "Error checking rate limit status",
                error=str(e),
                url=url
            )
            # Don't raise here unless it's a critical error
            if "closed" in str(e).lower():
                raise ScrapingError(f"Browser closed during rate limit check: {str(e)}")
    
    async def _wait_for_search_results(self, page) -> None:
        """Wait for search results to load completely."""
        try:
            # ✅ Check page state before waiting
            if page.is_closed():
                raise ScrapingError("Page closed before waiting for search results")
                
            # Wait for search results container
            await page.wait_for_selector(
                '.s-item__wrapper, .s-item, .srp-results',
                timeout=15000  # 15 seconds
            )
            
            # Additional wait for dynamic content
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            await self.logger.log_warning(
                "Could not detect search results load completion, proceeding with extraction"
            )
            # Don't raise here, proceed with extraction
    
    async def _extract_products_from_search(self, page, max_results: int) -> List[Product]:
        """Extract product data from search results page."""
        products = []
        
        try:
            # Find all product containers
            items = await page.query_selector_all(
                ".s-item__wrapper, .s-item"
            )
            
            if not items:
                await self.logger.log_warning("No product items found on page")
                return products
            
            # Limit to requested number of results
            items = items[:max_results]
            
            for i, item in enumerate(items):
                try:
                    product = await self._extract_product_from_element(item)
                    if product:
                        products.append(product)
                        
                        # Stop if we have enough products
                        if len(products) >= max_results:
                            break
                            
                except Exception as e:
                    await self.logger.log_warning(
                        f"Failed to extract product {i+1}",
                        error=str(e)
                    )
                    continue
            
            return products
            
        except Exception as e:
            await self.logger.log_error(
                "Failed to extract products from search page",
                error=str(e)
            )
        return products
    
    async def _extract_product_from_element(self, item_element) -> Optional[Product]:
        """Extract data for a single product item."""
        try:
            # Extract title
            title = await self._extract_text(item_element, [
                ".s-item__title",
                "h3 a",
                ".s-item__link"
            ])
            
            if not title or "Shop on eBay" in title:
                return None
            
            # Extract price
            price = await self._extract_price(item_element)
            
            # Extract item URL
            item_url = await self._extract_url(item_element)
            
            # Extract item ID from URL
            item_id = self._extract_item_id_from_url(item_url) if item_url else f"fallback_{hash(item_url) % 1000000}"
            
            # Extract image URL
            image_url = await self._extract_image_url(item_element)
            
            # Extract seller name
            seller_name = await self._extract_text(item_element, [
                ".s-item__seller-info-text",
                ".s-item__seller"
            ])
            
            # Extract shipping info
            shipping_cost, free_shipping = await self._extract_shipping_info(item_element)
            
            # Extract sold count (for sold listings)
            sold_count = await self._extract_sold_count(item_element)
            
            # Extract location
            location = await self._extract_text(item_element, [
                ".s-item__location",
                ".s-item__itemLocation"
            ])
            
            # Determine condition (simplified)
            condition = ProductCondition.UNKNOWN
            
            return Product(
                item_id=item_id,
                title=title,
                price=price or Decimal("0.00"),
                condition=condition,
                sold_count=sold_count,
                item_url=item_url,
                image_url=image_url,
                seller_name=seller_name or "Unknown",
                shipping_cost=shipping_cost,
                free_shipping=free_shipping,
                location=location or "Unknown",
                listing_date=datetime.utcnow() - timedelta(days=1)  # Approximate
            )
            
        except Exception as e:
            await self.logger.log_warning(
                "Failed to extract product data",
                error=str(e)
            )
            return None
    
    async def _extract_text(self, element, selectors: List[str]) -> Optional[str]:
        """Extract text from element using multiple selector fallbacks."""
        for selector in selectors:
            try:
                sub_element = await element.query_selector(selector)
                if sub_element:
                    text = await sub_element.text_content()
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        return None
    
    async def _extract_price(self, element) -> Optional[Decimal]:
        """Extract price from product element."""
        price_selectors = [
            ".s-item__price .notranslate",
            ".s-item__price",
            ".u-flL span",
            "[data-testid='s-item__price']"
        ]
        
        for selector in price_selectors:
            try:
                price_elem = await element.query_selector(selector)
                if price_elem:
                    price_text = await price_elem.text_content()
                    if price_text:
                        # Extract numeric price
                        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace('$', '').replace(',', ''))
                        if price_match:
                            return Decimal(price_match.group())
            except:
                continue
        
        return None
    
    async def _extract_url(self, element) -> Optional[str]:
        """Extract item URL from product element."""
        url_selectors = [
            ".s-item__link",
            "h3 a",
            "a[href*='/itm/']"
        ]
        
        for selector in url_selectors:
            try:
                link_elem = await element.query_selector(selector)
                if link_elem:
                    href = await link_elem.get_attribute("href")
                    if href:
                        return href
            except:
                continue
        
        return None
    
    def _extract_item_id_from_url(self, url: str) -> str:
        """Extract eBay item ID from URL."""
        try:
            # eBay URLs typically contain item ID after /itm/
            match = re.search(r'/itm/[^/]*?(\d{12,})', url)
            if match:
                return match.group(1)
        except:
            pass
        
        return f"unknown_{hash(url) % 1000000}"
    
    async def _extract_image_url(self, element) -> Optional[str]:
        """Extract product image URL."""
        img_selectors = [
            ".s-item__image img",
            "img[src*='ebayimg']",
            ".s-item__wrapper img"
        ]
        
        for selector in img_selectors:
            try:
                img_elem = await element.query_selector(selector)
                if img_elem:
                    src = await img_elem.get_attribute("src")
                    if src and "ebayimg" in src:
                        return src
            except:
                continue
        
        return None
    
    async def _extract_shipping_info(self, element) -> tuple[Optional[Decimal], bool]:
        """Extract shipping cost and free shipping flag."""
        shipping_selectors = [
            ".s-item__shipping",
            ".s-item__logisticsCost"
        ]
        
        for selector in shipping_selectors:
            try:
                shipping_elem = await element.query_selector(selector)
                if shipping_elem:
                    shipping_text = await shipping_elem.text_content()
                    if shipping_text:
                        if "free" in shipping_text.lower():
                            return None, True
                        
                        # Extract shipping cost
                        cost_match = re.search(r'\$?([\d,]+\.?\d*)', shipping_text)
                        if cost_match:
                            return Decimal(cost_match.group(1).replace(',', '')), False
            except:
                continue
        
        return None, False
    
    async def _extract_sold_count(self, element) -> Optional[int]:
        """Extract sold count from product element (for sold listings)."""
        sold_selectors = [
            ".s-item__sold",
            ".s-item__hotness",
            "[data-testid='s-item__sold']"
        ]
        
        for selector in sold_selectors:
            try:
                sold_elem = await element.query_selector(selector)
                if sold_elem:
                    sold_text = await sold_elem.text_content()
                    if sold_text:
                        # Extract number from "X sold" text
                        sold_match = re.search(r'(\d+)\s*sold', sold_text.lower())
                        if sold_match:
                            return int(sold_match.group(1))
            except:
                continue
        
        return None
    
    async def cleanup(self) -> None:
        """Clean up browser resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close() 