#!/usr/bin/env python3
"""
Real Amazon Scraper - Gerçekten çalışan Amazon scraper
Monitor ile entegre çalışır ve cache sistemi kullanır
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

CACHE_DIR = "scraping_cache"

class RealAmazonScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.page = None
        
    def log(self, message, level="info"):
        """Simple logging"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{level.upper()}] {message}")
        
    async def start(self):
        """Browser'ı başlat"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.page = await self.browser.new_page()
        
        # User agent ayarla
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.log("✅ Browser başlatıldı", "info")
        
    async def search_products(self, search_term, max_products=20):
        """Amazon'da ürün ara"""
        if not self.page:
            raise Exception("Browser başlatılmamış! Önce start() metodunu çağırın.")
            
        try:
            # Amazon ana sayfaya git
            url = "https://www.amazon.com"
            self.log(f"🌐 Amazon.com'a gidiliyor...", "info")
            
            await self.page.goto(url)
            await asyncio.sleep(2)
            
            # Arama kutusunu bul ve ara
            search_box = await self.page.query_selector('#twotabsearchtextbox')
            if search_box:
                await search_box.fill(search_term)
                await search_box.press('Enter')
                
                self.log(f"🔍 Aranan: {search_term}", "info")
                await asyncio.sleep(3)
                
                # Screenshot al
                os.makedirs(f"{CACHE_DIR}/screenshots", exist_ok=True)
                screenshot_path = f"{CACHE_DIR}/screenshots/amazon_latest.png"
                await self.page.screenshot(path=screenshot_path)
                
                # Ürünleri topla
                products = []
                items = await self.page.query_selector_all('[data-component-type="s-search-result"]')
                
                self.log(f"📦 {len(items)} ürün bulundu", "info")
                
                for i, item in enumerate(items[:max_products]):
                    try:
                        # Başlık
                        title_elem = await item.query_selector('h2 a span')
                        title = await title_elem.text_content() if title_elem else ""
                        
                        # Fiyat
                        price_elem = await item.query_selector('.a-price-whole')
                        if not price_elem:
                            price_elem = await item.query_selector('.a-price')
                        price_text = await price_elem.text_content() if price_elem else "0"
                        
                        # URL
                        link_elem = await item.query_selector('h2 a')
                        href = await link_elem.get_attribute('href') if link_elem else ""
                        url = f"https://www.amazon.com{href}" if href and not href.startswith('http') else href
                        
                        # Görsel
                        img_elem = await item.query_selector('img.s-image')
                        image = await img_elem.get_attribute('src') if img_elem else ""
                        
                        # Rating
                        rating_elem = await item.query_selector('.a-icon-alt')
                        rating_text = await rating_elem.text_content() if rating_elem else ""
                        
                        # Review count
                        review_elem = await item.query_selector('[aria-label*="stars"] + span')
                        review_text = await review_elem.text_content() if review_elem else "0"
                        
                        product = {
                            "title": title.strip() if title else "",
                            "price": self.extract_price(price_text),
                            "url": url,
                            "image_url": image,
                            "rating": self.extract_rating(rating_text),
                            "review_count": self.extract_review_count(review_text),
                            "platform": "amazon"
                        }
                        
                        products.append(product)
                        
                        title_display = title[:50] if title else "No title"
                        self.log(f"✅ {i+1}. ürün: {title_display}...", "info")
                        
                    except Exception as e:
                        self.log(f"⚠️ Ürün parse hatası: {str(e)}", "warning")
                        continue
                
                # Cache'e kaydet
                os.makedirs(CACHE_DIR, exist_ok=True)
                cache_file = f"{CACHE_DIR}/amazon_search_{search_term.replace(' ', '_')}.json"
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "search_term": search_term,
                        "timestamp": datetime.now().isoformat(),
                        "products": products
                    }, f, ensure_ascii=False, indent=2)
                
                self.log(f"💾 {len(products)} ürün cache'e kaydedildi", "info")
                
                return products
                
            else:
                self.log("❌ Arama kutusu bulunamadı", "error")
                return []
                
        except Exception as e:
            self.log(f"❌ Hata: {str(e)}", "error")
            raise
            
    def extract_price(self, price_text):
        """Fiyat metninden sayısal değer çıkar"""
        import re
        match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        return float(match.group()) if match else 0
        
    def extract_rating(self, rating_text):
        """Rating değerini çıkar"""
        import re
        match = re.search(r'(\d+\.?\d*)', rating_text)
        return float(match.group(1)) if match else 0
        
    def extract_review_count(self, review_text):
        """Review sayısını çıkar"""
        import re
        match = re.search(r'(\d+)', review_text.replace(',', ''))
        return int(match.group(1)) if match else 0
        
    async def close(self):
        """Browser'ı kapat"""
        if self.browser:
            await self.browser.close()
            self.log("🔴 Browser kapatıldı", "info")


async def test_scraper():
    """Test fonksiyonu"""
    scraper = RealAmazonScraper(headless=False)
    await scraper.start()
    
    try:
        # Bluetooth kulaklık ara
        products = await scraper.search_products("bluetooth headphones", max_products=10)
        print(f"\n✅ {len(products)} ürün bulundu!")
        
        for p in products[:3]:
            print(f"\n📦 {p['title']}")
            print(f"   💰 ${p['price']}")
            print(f"   ⭐ {p['rating']} ({p['review_count']} reviews)")
            
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(test_scraper()) 