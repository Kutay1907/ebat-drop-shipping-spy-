#!/usr/bin/env python3
"""
Background Scraper - Sürekli çalışan arkaplan scraping sistemi
Mock data kullanarak güvenilir çalışır
"""

import asyncio
import json
import os
import time
import requests
from datetime import datetime, timedelta
import logging

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('background_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackgroundScraper:
    def __init__(self):
        self.cache_dir = "scraping_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.monitor_url = "http://localhost:8082/api/update"
        
        # eBay kategorileri
        self.categories = [
            {"id": "293", "name": "Consumer Electronics"},
            {"id": "9355", "name": "Cell Phones & Accessories"}, 
            {"id": "11450", "name": "Clothing, Shoes & Accessories"},
            {"id": "15032", "name": "Computers/Tablets & Networking"},
            {"id": "11700", "name": "Home & Garden"},
            {"id": "1", "name": "Collectibles & Art"},
            {"id": "550", "name": "Art"},
            {"id": "2984", "name": "Baby"},
            {"id": "267", "name": "Books, Movies & Music"},
            {"id": "12576", "name": "Business & Industrial"}
        ]
        
        self.current_category_index = 0
        self.total_scraped = 0
        
    def update_monitor(self, platform, data):
        """Monitor'ü güncelle"""
        try:
            response = requests.post(self.monitor_url, json={f"{platform}_items": data.get("items", 0), f"{platform}_time": datetime.now().strftime("%H:%M:%S")}, timeout=2)
            if response.status_code == 200:
                logger.debug(f"Monitor updated: {platform}")
        except Exception as e:
            logger.debug(f"Monitor update failed: {e}")
    
    def generate_mock_ebay_products(self, category_name, count=20):
        """Mock eBay ürünleri oluştur"""
        products = []
        base_products = [
            {"title": "Wireless Bluetooth Headphones", "price": 59.99, "sold": 250},
            {"title": "USB-C Fast Charging Cable", "price": 24.99, "sold": 180},
            {"title": "Smartphone Case Premium", "price": 39.99, "sold": 120},
            {"title": "Portable Bluetooth Speaker", "price": 89.99, "sold": 95},
            {"title": "Wireless Mouse Ergonomic", "price": 29.99, "sold": 75},
            {"title": "Gaming Keyboard RGB", "price": 79.99, "sold": 65},
            {"title": "Phone Stand Adjustable", "price": 19.99, "sold": 150},
            {"title": "Power Bank 20000mAh", "price": 49.99, "sold": 85},
            {"title": "Car Phone Mount", "price": 15.99, "sold": 200},
            {"title": "Wireless Charger Pad", "price": 34.99, "sold": 110}
        ]
        
        for i in range(count):
            base = base_products[i % len(base_products)]
            product = {
                "title": f"{base['title']} {category_name} #{i+1}",
                "price": base["price"] + (i * 2.5),
                "sold_count": base["sold"] + i * 5,
                "url": f"https://ebay.com/item/{1000000 + i}",
                "image_url": f"https://i.ebayimg.com/images/g/mock{i}/s-l500.jpg",
                "seller": f"seller_{i % 10}",
                "condition": "New" if i % 3 == 0 else "Used"
            }
            products.append(product)
        
        return products
    
    def generate_mock_amazon_products(self, search_term, count=10):
        """Mock Amazon ürünleri oluştur"""
        products = []
        for i in range(count):
            product = {
                "title": f"Amazon {search_term} Product #{i+1}",
                "price": 25.99 + (i * 3.5),
                "rating": 4.0 + (i * 0.1),
                "reviews": 100 + (i * 20),
                "url": f"https://amazon.com/dp/B00MOCK{i:03d}",
                "image_url": f"https://m.media-amazon.com/images/mock{i}.jpg"
            }
            products.append(product)
        
        return products
    
    def save_to_cache(self, category_id, category_name, ebay_products, amazon_products):
        """Cache'e kaydet"""
        try:
            cache_data = {
                "category_id": category_id,
                "category_name": category_name,
                "timestamp": datetime.now().isoformat(),
                "ebay_products": ebay_products,
                "amazon_products": amazon_products,
                "total_products": len(ebay_products) + len(amazon_products)
            }
            
            filename = f"category_{category_id}_{category_name.lower().replace(' ', '_')}.json"
            filepath = os.path.join(self.cache_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Cache saved: {filename} ({len(ebay_products)} eBay + {len(amazon_products)} Amazon products)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache save failed: {e}")
            return False
    
    def scrape_category(self, category):
        """Bir kategoriyi scrape et"""
        category_id = category["id"]
        category_name = category["name"]
        
        logger.info(f"🔄 Scraping category: {category_name} ({category_id})")
        
        # Monitor'ü güncelle
        self.update_monitor("ebay", {"items": 0})
        self.update_monitor("amazon", {"items": 0})
        
        try:
            # eBay ürünleri oluştur
            logger.info(f"📦 Generating eBay products for {category_name}...")
            ebay_products = self.generate_mock_ebay_products(category_name, 25)
            self.update_monitor("ebay", {"items": len(ebay_products)})
            
            # Kısa bekleme
            time.sleep(2)
            
            # Amazon ürünleri oluştur
            logger.info(f"🛒 Generating Amazon products for {category_name}...")
            amazon_products = []
            
            # Her eBay ürünü için Amazon araması yap
            for ebay_product in ebay_products[:5]:  # İlk 5 ürün için
                search_term = ebay_product["title"].split()[0:3]  # İlk 3 kelime
                search_query = " ".join(search_term).lower()
                
                amazon_results = self.generate_mock_amazon_products(search_query, 2)
                amazon_products.extend(amazon_results)
                
                self.update_monitor("amazon", {"items": len(amazon_products)})
                time.sleep(1)  # Amazon API rate limiting simülasyonu
            
            # Cache'e kaydet
            if self.save_to_cache(category_id, category_name, ebay_products, amazon_products):
                self.total_scraped += len(ebay_products) + len(amazon_products)
                logger.info(f"✅ Category {category_name} completed: {len(ebay_products)} eBay + {len(amazon_products)} Amazon products")
                return True
            else:
                logger.error(f"❌ Failed to save category {category_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error scraping category {category_name}: {e}")
            return False
    
    def run_cycle(self):
        """Bir scraping döngüsü çalıştır"""
        logger.info(f"🚀 Starting scraping cycle - Category {self.current_category_index + 1}/{len(self.categories)}")
        
        # Mevcut kategoriyi al
        category = self.categories[self.current_category_index]
        
        # Kategoriyi scrape et
        success = self.scrape_category(category)
        
        # Sonraki kategoriye geç
        self.current_category_index = (self.current_category_index + 1) % len(self.categories)
        
        if success:
            logger.info(f"⏱️  Waiting 5 minutes before next category...")
            return 300  # 5 dakika bekle
        else:
            logger.info(f"⏱️  Error occurred, waiting 2 minutes before retry...")
            return 120  # 2 dakika bekle
    
    def run(self):
        """Ana çalışma döngüsü"""
        logger.info("🎯 Background Scraper started")
        logger.info(f"📁 Cache directory: {self.cache_dir}")
        logger.info(f"📊 Monitor URL: {self.monitor_url}")
        logger.info(f"🎯 Categories to scrape: {len(self.categories)}")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"🔄 Cycle #{cycle_count} starting...")
                
                wait_time = self.run_cycle()
                
                logger.info(f"📊 Total products scraped so far: {self.total_scraped}")
                logger.info(f"⏰ Waiting {wait_time} seconds...")
                
                # Bekleme süresi boyunca düzenli olarak monitor'ü güncelle
                for i in range(0, wait_time, 30):  # Her 30 saniyede bir
                    time.sleep(min(30, wait_time - i))
                    self.update_monitor("ebay", {"items": self.total_scraped // 2})
                    self.update_monitor("amazon", {"items": self.total_scraped // 2})
                
        except KeyboardInterrupt:
            logger.info("🛑 Background Scraper stopped by user")
        except Exception as e:
            logger.error(f"❌ Background Scraper crashed: {e}")
        finally:
            logger.info(f"📊 Final stats: {self.total_scraped} total products scraped")

if __name__ == "__main__":
    scraper = BackgroundScraper()
    scraper.run() 