"""
Amazon scraper module - REAL SCRAPING ONLY.
Removed all mock data, optimized for speed and reliability.
"""

import asyncio
import logging
import random
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import quote_plus
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from utils import clean_price_string, clean_title, get_random_user_agent, RateLimiter


@dataclass
class AmazonProduct:
    """Data class for Amazon product information."""
    title: str
    price: float
    url: str
    image_url: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    prime: bool = False


class AmazonScraper:
    """
    Amazon scraper class - REAL DATA ONLY.
    Optimized for speed and reliability.
    """
    
    def __init__(self, delay: float = 0.5, headless: bool = True):
        """
        Initialize Amazon scraper.
        
        Args:
            delay: Delay between requests in seconds (optimized for speed)
            headless: Whether to run browser in headless mode
        """
        self.delay = delay
        self.headless = headless
        self.logger = logging.getLogger(__name__)
        self.rate_limiter = RateLimiter(max_calls=15, time_window=60.0)  # More aggressive
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_browser()
    
    async def start_browser(self) -> None:
        """Start Playwright browser."""
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images'  # Faster loading
                ]
            )
            self.logger.info("Amazon browser started")
    
    async def close_browser(self) -> None:
        """Close Playwright browser safely."""
        try:
            if self.browser:
                try:
                    await self.browser.close()
                except:
                    pass
                self.browser = None
            if self.playwright:
                try:
                    await self.playwright.stop()
                except:
                    pass
                self.playwright = None
            self.logger.info("✅ Amazon browser closed")
        except Exception as e:
            self.logger.warning(f"⚠️ Error closing Amazon browser (non-critical): {e}")
    
    def build_search_url(self, search_term: str) -> str:
        """Build Amazon search URL."""
        encoded_term = quote_plus(search_term)
        return f"https://www.amazon.com/s?k={encoded_term}&ref=sr_pg_1"
    
    async def search_products(self, search_term: str, max_results: int = 5) -> List[AmazonProduct]:
        """
        Search for products by scraping Amazon - REAL DATA ONLY.
        
        Args:
            search_term: Search query
            max_results: Maximum number of results
        
        Returns:
            List of AmazonProduct objects
        """
        products = []
        
        try:
            # Ensure fresh browser
            await self.start_browser()
            
            if not self.browser:
                self.logger.error("❌ Failed to start browser")
                return []
            
            await self.rate_limiter.wait_if_needed()
            
            url = self.build_search_url(search_term)
            self.logger.info(f"🔍 Searching Amazon for: {search_term}")
            
            page = await self.browser.new_page()
            page.set_default_timeout(15000)  # 15 seconds
            
            await page.goto(url, wait_until='domcontentloaded')
            
            # Quick bot detection check
            page_content = await page.content()
            if "robot" in page_content.lower() or "captcha" in page_content.lower():
                self.logger.warning("⚠️ Amazon blocked request")
                await page.close()
                return products
            
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Fast product extraction
            product_containers = soup.find_all('div', {
                'data-component-type': 's-search-result'
            })
            
            if not product_containers:
                product_containers = soup.find_all('div', class_='s-result-item')
            
            if not product_containers:
                product_containers = soup.find_all('div', attrs={'data-asin': True})
            
            if not product_containers:
                self.logger.warning("⚠️ No product containers found")
                await page.close()
                return products
            
            self.logger.info(f"📦 Found {len(product_containers)} product containers")
            
            # Fast extraction
            for i, container in enumerate(product_containers[:max_results * 2]):
                if len(products) >= max_results:
                    break
                
                try:
                    product = await self.extract_product_fast(soup, container)
                    if product:
                        products.append(product)
                        self.logger.info(f"✅ Found: {product.title[:30]}... - ${product.price}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Error extracting product {i}: {e}")
                    continue
            
            # Sort by price (lowest first)
            products.sort(key=lambda x: x.price)
            await page.close()
            
        except Exception as e:
            self.logger.error(f"❌ Error searching Amazon: {e}")
        finally:
            # Always close browser
            await self.close_browser()
        
        return products[:max_results]
    
    async def extract_product_fast(self, soup, product_element) -> Optional[AmazonProduct]:
        """Fast product extraction with minimal processing."""
        try:
            # Title - try multiple selectors quickly
            title_selectors = [
                'h2 a span',
                '.a-size-medium',
                'h2.s-size-mini span',
                '.a-link-normal span'
            ]
            
            title = None
            for selector in title_selectors:
                try:
                    title_elem = product_element.find(class_=selector.replace('.', '').replace('h2 a ', '').replace('span', ''))
                    if not title_elem:
                        # Try CSS selector approach
                        if selector.startswith('h2'):
                            title_elem = product_element.find('h2')
                            if title_elem:
                                span = title_elem.find('span')
                                if span:
                                    title_elem = span
                    
                    if title_elem:
                        title = clean_title(title_elem.get_text(strip=True))
                        if title and len(title) > 10:  # Valid title
                            break
                except:
                    continue
            
            if not title:
                return None
            
            # Price - fast extraction
            price_selectors = [
                'a-price-whole',
                'a-price',
                'a-offscreen'
            ]
            
            price = None
            for selector in price_selectors:
                try:
                    price_elem = product_element.find(class_=selector)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        
                        # Check for fraction
                        fraction_elem = product_element.find(class_='a-price-fraction')
                        if fraction_elem:
                            price_text += '.' + fraction_elem.get_text(strip=True)
                        
                        price = clean_price_string(price_text)
                        if price and price > 0:
                            break
                except:
                    continue
            
            if not price or price <= 0:
                return None
            
            # URL - simple extraction
            url = "https://www.amazon.com"
            try:
                link_elem = product_element.find('a', href=True)
                if link_elem and 'href' in link_elem.attrs:
                    href = link_elem['href']
                    if href.startswith('/'):
                        url = f"https://www.amazon.com{href}"
                    elif href.startswith('http'):
                        url = href
            except:
                pass
            
            # Rating - optional, fast
            rating = None
            try:
                rating_elem = product_element.find(class_='a-icon-alt')
                if rating_elem:
                    rating_text = rating_elem.get_text()
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                        if rating > 5:
                            rating = rating / 2
            except:
                pass
            
            # Reviews count - optional, fast
            reviews_count = None
            try:
                reviews_elem = product_element.find('a', href=lambda x: x and '#customerReviews' in x)
                if reviews_elem:
                    reviews_text = reviews_elem.get_text()
                    reviews_match = re.search(r'(\d+)', reviews_text.replace(',', ''))
                    if reviews_match:
                        reviews_count = int(reviews_match.group(1))
            except:
                pass
            
            # Prime - fast check
            prime = product_element.find(class_='a-icon-prime') is not None
            
            return AmazonProduct(
                title=title,
                price=price,
                url=url,
                rating=rating,
                reviews_count=reviews_count,
                prime=prime
            )
            
        except Exception as e:
            self.logger.warning(f"Error extracting Amazon product: {e}")
            return None
    
    async def find_cheapest_match(self, search_term: str) -> Optional[AmazonProduct]:
        """Find the cheapest matching product on Amazon."""
        products = await self.search_products(search_term, max_results=10)
        
        if not products:
            return None
        
        return products[0]  # Already sorted by price

    def calculate_profit_margin_percentage(self, ebay_price: float, amazon_price: float) -> float:
        """Calculate profit margin percentage."""
        if amazon_price <= 0:
            return 0.0
        
        profit = ebay_price - amazon_price
        margin_percentage = (profit / amazon_price) * 100
        return round(margin_percentage, 2)

    def is_profitable_with_minimum_margin(self, ebay_price: float, amazon_price: float, 
                                        min_margin_percentage: float = 50.0) -> bool:
        """Check if profitable with minimum margin."""
        margin = self.calculate_profit_margin_percentage(ebay_price, amazon_price)
        return margin >= min_margin_percentage


# Example usage function
async def main():
    """Example usage of the Amazon scraper."""
    import re
    from utils import setup_logging
    
    logger = setup_logging("INFO")
    
    async with AmazonScraper(delay=0.5, headless=True) as scraper:
        # Test search
        search_terms = [
            "bluetooth headphones",
            "usb cable",
            "phone stand",
            "wireless mouse"
        ]
        
        for term in search_terms:
            print(f"\nSearching for: {term}")
            products = await scraper.search_products(term, max_results=3)
            
            for i, product in enumerate(products, 1):
                print(f"{i}. {product.title}")
                print(f"   Price: ${product.price:.2f}")
                print(f"   Prime: {product.prime}")
                print(f"   URL: {product.url}")
            
            # Find cheapest
            cheapest = await scraper.find_cheapest_match(term)
            if cheapest:
                print(f"Cheapest: ${cheapest.price:.2f} - {cheapest.title}")


if __name__ == "__main__":
    asyncio.run(main()) 