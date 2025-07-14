"""
Amazon Product Scraper Service
============================

A comprehensive service for scraping Amazon product pages and extracting
clean, structured data suitable for eBay listing creation.

Features:
- Scrapes title, images, description, price, and item specifics
- Cleans image URLs to remove Amazon CDN references
- Optimizes titles to 80 characters for eBay compliance
- Extracts and structures product features and specifications
- Handles different Amazon page layouts and formats
"""

import re
import logging
import asyncio
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class AmazonScraperError(Exception):
    """Custom exception for Amazon scraping errors."""
    pass

class AmazonProductScraper:
    """
    Advanced Amazon product scraper using multiple strategies for robust data extraction.
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def scrape_product(self, amazon_url: str) -> Dict[str, Any]:
        """
        Main method to scrape Amazon product data.
        
        Args:
            amazon_url: Amazon product URL (can be any format)
            
        Returns:
            Dictionary containing cleaned product data
        """
        try:
            # Clean and validate URL
            clean_url = self._clean_amazon_url(amazon_url)
            logger.info(f"Scraping Amazon product: {clean_url}")
            
            # Try Playwright first (more reliable for complex pages)
            try:
                product_data = await self._scrape_with_playwright(clean_url)
                if product_data.get('title'):
                    return product_data
            except Exception as e:
                logger.warning(f"Playwright scraping failed: {e}")
            
            # Fallback to requests + BeautifulSoup
            try:
                product_data = await self._scrape_with_requests(clean_url)
                if product_data.get('title'):
                    return product_data
            except Exception as e:
                logger.warning(f"Requests scraping failed: {e}")
            
            raise AmazonScraperError("Failed to scrape product data with all methods")
            
        except Exception as e:
            logger.error(f"Error scraping Amazon product: {e}")
            raise AmazonScraperError(f"Scraping failed: {str(e)}")
    
    def _clean_amazon_url(self, url: str) -> str:
        """Clean Amazon URL to standard format."""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Extract ASIN from various Amazon URL formats
        asin_patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'ASIN=([A-Z0-9]{10})',
            r'/([A-Z0-9]{10})/?(?:\?|$)'
        ]
        
        for pattern in asin_patterns:
            match = re.search(pattern, url)
            if match:
                asin = match.group(1)
                return f"https://www.amazon.com/dp/{asin}"
        
        # If no ASIN found, return original URL
        return url
    
    async def _scrape_with_playwright(self, url: str) -> Dict[str, Any]:
        """Scrape using Playwright for JavaScript-heavy pages."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set user agent and other headers
            await page.set_extra_http_headers(self.headers)
            
            # Navigate to the page
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for key elements to load
            try:
                await page.wait_for_selector('#productTitle', timeout=10000)
            except:
                pass  # Continue even if title not found immediately
            
            # Get page content
            content = await page.content()
            await browser.close()
            
            return self._parse_amazon_html(content)
    
    async def _scrape_with_requests(self, url: str) -> Dict[str, Any]:
        """Scrape using requests + BeautifulSoup as fallback."""
        async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            return self._parse_amazon_html(response.text)
    
    def _parse_amazon_html(self, html_content: str) -> Dict[str, Any]:
        """Parse Amazon HTML and extract product data."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        product_data = {
            'title': self._extract_title(soup),
            'price': self._extract_price(soup),
            'images': self._extract_images(soup),
            'description': self._extract_description(soup),
            'specifics': self._extract_specifics(soup)
        }
        
        # Validate that we got some data
        if not product_data['title']:
            raise AmazonScraperError("Could not extract product title")
        
        return product_data
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract and optimize product title."""
        title_selectors = [
            '#productTitle',
            '.product-title',
            '[data-automation-id="product-title"]',
            'h1.a-size-large',
            'h1 span'
        ]
        
        title = ""
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                break
        
        if not title:
            return ""
        
        # Clean and optimize title for eBay (80 characters max)
        title = self._clean_title(title)
        return self._optimize_title_length(title, 80)
    
    def _clean_title(self, title: str) -> str:
        """Clean title from Amazon-specific text."""
        # Remove common Amazon-specific phrases
        remove_phrases = [
            r'\s*-\s*Amazon\.com.*$',
            r'\s*\|\s*Amazon.*$',
            r'\s*on Amazon.*$',
            r'\s*Amazon\'s Choice.*$',
            r'\s*\(.*pack.*\)$',  # Remove pack info that takes up space
            r'\s*\[.*\]$',  # Remove brackets at end
        ]
        
        for pattern in remove_phrases:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    def _optimize_title_length(self, title: str, max_length: int) -> str:
        """Optimize title to fit within character limit while maintaining meaning."""
        if len(title) <= max_length:
            return title
        
        # Try to truncate at word boundaries
        words = title.split()
        optimized = ""
        
        for word in words:
            if len(optimized + " " + word) <= max_length:
                optimized += (" " + word) if optimized else word
            else:
                break
        
        # If still too long, hard truncate and add ellipsis
        if len(optimized) > max_length - 3:
            optimized = optimized[:max_length - 3] + "..."
        
        return optimized
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract product price."""
        price_selectors = [
            '.a-price-whole',
            '.a-price .a-offscreen',
            '#price_inside_buybox',
            '.a-price-current',
            '[data-automation-id="price"]',
            '.a-price-symbol + .a-price-whole'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text().strip()
                price = self._parse_price(price_text)
                if price:
                    return price
        
        return None
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text."""
        # Remove currency symbols and extract number
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            try:
                return float(price_match.group())
            except ValueError:
                pass
        
        return None
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract product images and clean URLs."""
        images = []
        
        # Try different image selectors
        image_selectors = [
            '#landingImage',
            '#imgBlkFront',
            '.a-dynamic-image',
            '[data-action="main-image-click"] img',
            '#altImages img'
        ]
        
        # Also look for image data in script tags
        script_images = self._extract_images_from_scripts(soup)
        
        for selector in image_selectors:
            elements = soup.select(selector)
            for img in elements:
                src = img.get('src') or img.get('data-src') or img.get('data-old-hires')
                if src and isinstance(src, str):
                    clean_url = self._clean_image_url(src)
                    if clean_url and clean_url not in images:
                        images.append(clean_url)
        
        # Add script images
        for img_url in script_images:
            clean_url = self._clean_image_url(img_url)
            if clean_url and clean_url not in images:
                images.append(clean_url)
        
        # Limit to first 12 images (eBay limit)
        return images[:12]
    
    def _extract_images_from_scripts(self, soup: BeautifulSoup) -> List[str]:
        """Extract image URLs from JavaScript variables."""
        images = []
        
        scripts = soup.find_all('script')
        for script in scripts:
            script_text = script.get_text() if script else ""
            if script_text:
                # Look for image data in various JavaScript patterns
                patterns = [
                    r'"hiRes":"([^"]+)"',
                    r'"large":"([^"]+)"',
                    r'"main":{"[^"]+":"([^"]+)"'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, script_text)
                    images.extend(matches)
        
        return images
    
    def _clean_image_url(self, url: str) -> Optional[str]:
        """Clean image URL to remove Amazon CDN and get direct link."""
        if not url or 'amazon' not in url:
            return None
        
        # Remove Amazon-specific parameters
        if '._' in url:
            url = url.split('._')[0] + '.jpg'
        
        # Ensure HTTPS
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            return None  # Skip relative URLs
        
        # Basic validation
        if url.startswith('https://') and any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            return url
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract and clean product description."""
        description_parts = []
        
        # Extract feature bullets
        feature_bullets = self._extract_feature_bullets(soup)
        if feature_bullets:
            description_parts.append("<ul>")
            for bullet in feature_bullets[:8]:  # Limit bullets
                description_parts.append(f"<li>{bullet}</li>")
            description_parts.append("</ul>")
        
        # Extract product description
        desc_selectors = [
            '#feature-bullets ul',
            '#productDescription',
            '[data-automation-id="productDescription"]',
            '.a-expander-content',
            '.product-description'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                desc_text = self._clean_html_content(element)
                if desc_text and desc_text not in description_parts:
                    description_parts.append(desc_text)
                break
        
        return "<br>".join(description_parts) if description_parts else ""
    
    def _extract_feature_bullets(self, soup: BeautifulSoup) -> List[str]:
        """Extract feature bullet points."""
        bullets = []
        
        bullet_selectors = [
            '#feature-bullets li span',
            '.a-unordered-list .a-list-item',
            '[data-automation-id="feature-bullet"]'
        ]
        
        for selector in bullet_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 10 and text not in bullets:
                    bullets.append(self._clean_text(text))
        
        return bullets[:8]  # Limit to 8 bullets
    
    def _extract_specifics(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract item specifics like brand, dimensions, etc."""
        specifics = {}
        
        # Try technical details table
        tech_table = soup.select_one('#prodDetails table, .a-keyvalue')
        if tech_table:
            rows = tech_table.select('tr')
            for row in rows:
                cells = row.select('td, th')
                if len(cells) >= 2:
                    key = self._clean_text(cells[0].get_text())
                    value = self._clean_text(cells[1].get_text())
                    if key and value:
                        specifics[key] = value
        
        # Extract brand
        brand_selectors = ['#bylineInfo', '.a-row .a-size-base', '[data-automation-id="brand-name"]']
        for selector in brand_selectors:
            element = soup.select_one(selector)
            if element:
                brand_text = element.get_text().strip()
                if 'brand' in brand_text.lower() or 'visit' in brand_text.lower():
                    brand = re.sub(r'(visit|brand|store)', '', brand_text, flags=re.IGNORECASE).strip()
                    if brand:
                        specifics['Brand'] = brand
                        break
        
        return specifics
    
    def _clean_html_content(self, element) -> str:
        """Clean HTML content for eBay description."""
        # Remove script and style elements
        for script in element(["script", "style"]):
            script.decompose()
        
        # Get text and basic HTML
        text = str(element)
        
        # Clean up HTML - keep only basic formatting
        allowed_tags = ['p', 'br', 'ul', 'li', 'ol', 'strong', 'b', 'i', 'em']
        cleaned = re.sub(r'<(?!/?(?:' + '|'.join(allowed_tags) + r')\b)[^>]*>', '', text)
        
        return self._clean_text(cleaned)
    
    def _clean_text(self, text: str) -> str:
        """Clean text content."""
        # Remove extra whitespace and clean up
        text = re.sub(r'\s+', ' ', text).strip()
        text = text.replace('\n', ' ').replace('\t', ' ')
        
        # Remove common unwanted phrases
        unwanted_phrases = [
            'See more product details',
            'Visit the Store',
            'Amazon\'s Choice',
            'Climate Pledge Friendly'
        ]
        
        for phrase in unwanted_phrases:
            text = text.replace(phrase, '')
        
        return text.strip()

# Global instance
amazon_scraper = AmazonProductScraper() 