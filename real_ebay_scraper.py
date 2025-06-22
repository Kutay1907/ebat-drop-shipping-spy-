#!/usr/bin/env python3
"""
Real eBay Scraper - Gerçekten çalışan eBay scraper
Monitor ile entegre çalışır ve cache sistemi kullanır
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
import requests

CACHE_DIR = "scraping_cache"
MONITOR_URL = "http://localhost:8082"

class RealEbayScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.page = None
        
    def log(self, message, level="info"):
        """Log to console and monitor"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{level.upper()}] {message}")
        
        # Send to monitor
        try:
            requests.post(f"{MONITOR_URL}/api/log/ebay", 
                         json={"message": message, "level": level},
                         timeout=1)
        except:
            pass  # Ignore monitor errors
            
    def update_monitor(self, **kwargs):
        """Update monitor status"""
        try:
            requests.post(f"{MONITOR_URL}/api/update/ebay", 
                         json=kwargs,
                         timeout=1)
        except:
            pass
        
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
        self.update_monitor(active=True)
        
    async def scrape_category(self, category_id, max_products=20):
        """eBay kategorisinden ürün scrape et"""
        if not self.page:
            raise Exception("Browser başlatılmamış! Önce start() metodunu çağırın.")
            
        try:
            # URL oluştur
            url = f"https://www.ebay.com/sch/i.html?_sacat={category_id}&_sop=12&_ipg=50"
            
            self.log(f"🌐 URL: {url}", "info")
            self.update_monitor(current_url=url)
            
            # Sayfaya git
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)
            
            # Screenshot al
            os.makedirs(f"{CACHE_DIR}/screenshots", exist_ok=True)
            screenshot_path = f"{CACHE_DIR}/screenshots/ebay_latest.png"
            await self.page.screenshot(path=screenshot_path)
            self.update_monitor(screenshot=True)
            
            # Ürünleri bul
            products = []
            items = await self.page.query_selector_all('.s-item')
            
            self.log(f"📦 {len(items)} ürün bulundu", "info")
            
            for i, item in enumerate(items[:max_products]):
                try:
                    # Başlık
                    title_elem = await item.query_selector('.s-item__title')
                    title = await title_elem.text_content() if title_elem else ""
                    
                    # Skip "Shop on eBay" items
                    if title and "Shop on eBay" in title:
                        continue
                    
                    # Fiyat
                    price_elem = await item.query_selector('.s-item__price')
                    price_text = await price_elem.text_content() if price_elem else "0"
                    
                    # Satış sayısı
                    sold_elem = await item.query_selector('.s-item__hotness, .s-item__quantitySold')
                    sold_text = await sold_elem.text_content() if sold_elem else "0 sold"
                    
                    # URL
                    link_elem = await item.query_selector('.s-item__link')
                    url = await link_elem.get_attribute('href') if link_elem else ""
                    
                    # Görsel
                    img_elem = await item.query_selector('.s-item__image img')
                    image = await img_elem.get_attribute('src') if img_elem else ""
                    
                    # Satıcı bilgisi
                    seller_elem = await item.query_selector('.s-item__seller-info')
                    seller = await seller_elem.text_content() if seller_elem else "Unknown"
                    
                    product = {
                        "title": title.strip() if title else "",
                        "price": self.extract_price(price_text),
                        "sold_count": self.extract_sold_count(sold_text),
                        "url": url,
                        "image_url": image,
                        "seller": seller.strip() if seller else "Unknown",
                        "platform": "ebay"
                    }
                    
                    products.append(product)
                    self.update_monitor(items_found=len(products))
                    
                    # Title kontrolü
                    title_display = title[:50] if title else "No title"
                    self.log(f"✅ {i+1}. ürün: {title_display}...", "info")
                    
                except Exception as e:
                    self.log(f"⚠️ Ürün parse hatası: {str(e)}", "warning")
                    continue
            
            # Cache'e kaydet
            os.makedirs(CACHE_DIR, exist_ok=True)
            cache_file = f"{CACHE_DIR}/ebay_category_{category_id}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "category_id": category_id,
                    "timestamp": datetime.now().isoformat(),
                    "products": products
                }, f, ensure_ascii=False, indent=2)
            
            self.log(f"💾 {len(products)} ürün cache'e kaydedildi", "info")
            
            return products
            
        except Exception as e:
            self.log(f"❌ Hata: {str(e)}", "error")
            raise
            
    def extract_price(self, price_text):
        """Fiyat metninden sayısal değer çıkar"""
        import re
        match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        return float(match.group()) if match else 0
        
    def extract_sold_count(self, sold_text):
        """Satış sayısını çıkar"""
        import re
        match = re.search(r'(\d+)', sold_text)
        return int(match.group(1)) if match else 0
        
    async def close(self):
        """Browser'ı kapat"""
        if self.browser:
            await self.browser.close()
            self.log("🔴 Browser kapatıldı", "info")
            self.update_monitor(active=False)


async def test_scraper():
    """Test fonksiyonu"""
    scraper = RealEbayScraper(headless=False)
    await scraper.start()
    
    try:
        # Elektronik kategorisini scrape et
        products = await scraper.scrape_category("293", max_products=10)
        print(f"\n✅ {len(products)} ürün bulundu!")
        
        for p in products[:3]:
            print(f"\n📦 {p['title']}")
            print(f"   💰 ${p['price']}")
            print(f"   📊 {p['sold_count']} satış")
            
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(test_scraper()) 