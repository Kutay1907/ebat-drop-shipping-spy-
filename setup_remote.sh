#!/bin/bash

# eBay Dropshipping Spy - Uzak Bilgisayar Kurulum Scripti
# Bu script sistemi başka bir bilgisayarda kurmanız için hazırlanmıştır

echo "🏠 eBay Dropshipping Spy - Evdeki Başka Bilgisayar Kurulumu"
echo "============================================================"
echo ""

# Sistem bilgilerini kontrol et
echo "📋 Sistem bilgileri kontrol ediliyor..."
echo "OS: $(uname -s)"
echo "Architecture: $(uname -m)"
echo "Python Version: $(python3 --version 2>/dev/null || echo 'Python3 bulunamadı')"
echo ""

# Python3 kontrolü
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 bulunamadı!"
    echo "📥 Python3 kurulumu gerekli:"
    echo ""
    echo "macOS için:"
    echo "  brew install python3"
    echo ""
    echo "Ubuntu/Debian için:"
    echo "  sudo apt update && sudo apt install python3 python3-pip"
    echo ""
    echo "Windows için:"
    echo "  https://python.org adresinden Python 3.8+ indirin"
    echo ""
    exit 1
fi

# Pip kontrolü
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 bulunamadı!"
    echo "📥 pip kurulumu:"
    echo "  curl https://bootstrap.pypa.io/get-pip.py | python3"
    exit 1
fi

echo "✅ Python3 ve pip3 mevcut"
echo ""

# Proje dizini oluştur
PROJECT_DIR="$HOME/eBay_Dropshipping_Spy"
echo "📁 Proje dizini oluşturuluyor: $PROJECT_DIR"

if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️  Dizin zaten mevcut. Yedek alınıyor..."
    mv "$PROJECT_DIR" "${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "✅ Proje dizini hazır: $(pwd)"
echo ""

# Gerekli dosyaları oluştur
echo "📝 Gerekli dosyalar oluşturuluyor..."

# requirements.txt
cat > requirements.txt << 'EOF'
flask==2.3.3
requests==2.31.0
playwright==1.40.0
beautifulsoup4==4.12.2
fake-useragent==1.4.0
pillow==10.0.1
python-dotenv==1.0.0
EOF

# Simple Monitor
cat > simple_monitor.py << 'EOF'
#!/usr/bin/env python3
"""
Simple Scraping Monitor - Hızlı ve güvenilir scraping monitor
Port: 8082
"""

import json
import os
from datetime import datetime
from flask import Flask, render_template_string, jsonify
import logging

# Minimal logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Basit HTML template (burada template kodu olacak - kısaltılmış)
MONITOR_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>🖥️ Scraping Monitor</title>
    <style>
        body { background: linear-gradient(135deg, #0c1445 0%, #1a237e 100%); color: #fff; font-family: 'Segoe UI', sans-serif; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .card { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; margin: 10px; }
        .metric-value { font-size: 2em; font-weight: bold; color: #00ff00; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ Scraping Monitor</h1>
            <p>eBay ve Amazon scraping işlemlerini canlı izleyin</p>
        </div>
        <div class="card">
            <h3>📊 Sistem Durumu</h3>
            <p>eBay Ürünleri: <span id="ebay-count" class="metric-value">{{ ebay_count }}</span></p>
            <p>Amazon Ürünleri: <span id="amazon-count" class="metric-value">{{ amazon_count }}</span></p>
            <p>Cache Dosyaları: <span id="cache-count" class="metric-value">{{ cache_count }}</span></p>
            <p>Son Güncelleme: <span id="last-update">{{ current_time }}</span></p>
        </div>
    </div>
    <script>
        setInterval(() => {
            fetch('/api/status').then(r => r.json()).then(data => {
                document.getElementById('ebay-count').textContent = data.ebay_items || 0;
                document.getElementById('amazon-count').textContent = data.amazon_items || 0;
                document.getElementById('cache-count').textContent = data.cache_files || 0;
                document.getElementById('last-update').textContent = data.current_time || '--:--';
            });
        }, 5000);
    </script>
</body>
</html>
"""

# Global status
monitor_status = {"ebay_items": 0, "amazon_items": 0, "cache_files": 0}

@app.route('/')
def index():
    cache_count = len([f for f in os.listdir("scraping_cache") if f.endswith('.json')]) if os.path.exists("scraping_cache") else 0
    return render_template_string(MONITOR_HTML, 
                                ebay_count=monitor_status.get("ebay_items", 0),
                                amazon_count=monitor_status.get("amazon_items", 0),
                                cache_count=cache_count,
                                current_time=datetime.now().strftime("%H:%M:%S"))

@app.route('/api/status')
def get_status():
    cache_count = len([f for f in os.listdir("scraping_cache") if f.endswith('.json')]) if os.path.exists("scraping_cache") else 0
    monitor_status["cache_files"] = cache_count
    monitor_status["current_time"] = datetime.now().strftime("%H:%M:%S")
    return jsonify(monitor_status)

@app.route('/api/update', methods=['POST'])
def update_status():
    from flask import request
    data = request.get_json()
    if data:
        monitor_status.update(data)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print("🖥️  Simple Monitor: http://localhost:8082")
    app.run(debug=False, host='0.0.0.0', port=8082, threaded=True)
EOF

# Background Scraper (kısaltılmış versiyon)
cat > background_scraper.py << 'EOF'
#!/usr/bin/env python3
"""
Background Scraper - Sürekli çalışan arkaplan scraping sistemi
"""

import json
import os
import time
import requests
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackgroundScraper:
    def __init__(self):
        self.cache_dir = "scraping_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.monitor_url = "http://localhost:8082/api/update"
        self.categories = [
            {"id": "293", "name": "Consumer Electronics"},
            {"id": "9355", "name": "Cell Phones & Accessories"},
            {"id": "11450", "name": "Clothing, Shoes & Accessories"},
            {"id": "15032", "name": "Computers/Tablets & Networking"},
            {"id": "11700", "name": "Home & Garden"}
        ]
        self.current_index = 0
        self.total_scraped = 0
    
    def update_monitor(self, platform, data):
        try:
            requests.post(self.monitor_url, json={f"{platform}_items": data.get("items", 0)}, timeout=2)
        except:
            pass
    
    def generate_mock_products(self, category_name, count=20):
        products = []
        for i in range(count):
            products.append({
                "title": f"Mock Product {category_name} #{i+1}",
                "price": 25.99 + (i * 2.5),
                "sold_count": 50 + (i * 5),
                "url": f"https://ebay.com/item/{1000000 + i}"
            })
        return products
    
    def scrape_category(self, category):
        logger.info(f"🔄 Scraping: {category['name']}")
        
        # Mock eBay products
        ebay_products = self.generate_mock_products(category["name"], 25)
        self.update_monitor("ebay", {"items": len(ebay_products)})
        time.sleep(2)
        
        # Mock Amazon products  
        amazon_products = self.generate_mock_products(f"Amazon {category['name']}", 10)
        self.update_monitor("amazon", {"items": len(amazon_products)})
        
        # Cache'e kaydet
        cache_data = {
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "ebay_products": ebay_products,
            "amazon_products": amazon_products
        }
        
        filename = f"category_{category['id']}.json"
        with open(os.path.join(self.cache_dir, filename), 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        self.total_scraped += len(ebay_products) + len(amazon_products)
        logger.info(f"✅ {category['name']} completed: {self.total_scraped} total products")
        return True
    
    def run(self):
        logger.info("🎯 Background Scraper started")
        try:
            while True:
                category = self.categories[self.current_index]
                self.scrape_category(category)
                self.current_index = (self.current_index + 1) % len(self.categories)
                logger.info("⏱️  Waiting 5 minutes...")
                time.sleep(300)  # 5 dakika bekle
        except KeyboardInterrupt:
            logger.info("🛑 Stopped by user")

if __name__ == "__main__":
    scraper = BackgroundScraper()
    scraper.run()
EOF

# Başlatma scripti
cat > start_system.sh << 'EOF'
#!/bin/bash

echo "🚀 eBay Dropshipping Spy Başlatılıyor..."

# Monitor'ü başlat
echo "📊 Monitor başlatılıyor (Port: 8082)..."
python3 simple_monitor.py &
MONITOR_PID=$!
echo "Monitor PID: $MONITOR_PID"

# 2 saniye bekle
sleep 2

# Background scraper'ı başlat
echo "🔄 Background scraper başlatılıyor..."
python3 background_scraper.py &
SCRAPER_PID=$!
echo "Scraper PID: $SCRAPER_PID"

# PID'leri kaydet
echo $MONITOR_PID > monitor.pid
echo $SCRAPER_PID > scraper.pid

echo ""
echo "✅ Sistem başarıyla başlatıldı!"
echo "📊 Monitor: http://localhost:8082"
echo "📝 Loglar: background_scraper.log"
echo ""
echo "Durdurmak için: ./stop_system.sh"
EOF

# Durdurma scripti
cat > stop_system.sh << 'EOF'
#!/bin/bash

echo "🛑 eBay Dropshipping Spy Durduruluyor..."

# PID dosyalarını kontrol et
if [ -f "monitor.pid" ]; then
    MONITOR_PID=$(cat monitor.pid)
    kill $MONITOR_PID 2>/dev/null && echo "Monitor durduruldu (PID: $MONITOR_PID)"
    rm monitor.pid
fi

if [ -f "scraper.pid" ]; then
    SCRAPER_PID=$(cat scraper.pid)
    kill $SCRAPER_PID 2>/dev/null && echo "Scraper durduruldu (PID: $SCRAPER_PID)"
    rm scraper.pid
fi

echo "✅ Sistem durduruldu"
EOF

# Scriptleri çalıştırılabilir yap
chmod +x start_system.sh stop_system.sh

echo "✅ Temel dosyalar oluşturuldu"
echo ""

# Python paketlerini kur
echo "📦 Python paketleri kuruluyor..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Python paketleri kuruldu"
else
    echo "❌ Paket kurulumu başarısız"
    echo "Manuel kurulum: pip3 install -r requirements.txt"
fi

echo ""

# Dizin yapısını oluştur
mkdir -p scraping_cache
mkdir -p logs

echo "📁 Dizin yapısı oluşturuldu"
echo ""

# Test çalıştır
echo "🧪 Sistem testi yapılıyor..."
python3 -c "
import flask, requests
print('✅ Flask ve requests çalışıyor')
"

if [ $? -eq 0 ]; then
    echo "✅ Temel test başarılı"
else
    echo "❌ Test başarısız - paket kurulumunu kontrol edin"
fi

echo ""
echo "🎉 KURULUM TAMAMLANDI!"
echo "======================================"
echo ""
echo "📍 Kurulum dizini: $(pwd)"
echo ""
echo "🚀 Sistemi başlatmak için:"
echo "   ./start_system.sh"
echo ""
echo "🛑 Sistemi durdurmak için:"
echo "   ./stop_system.sh"
echo ""
echo "📊 Monitor adresi:"
echo "   http://localhost:8082"
echo ""
echo "📝 Log dosyası:"
echo "   tail -f background_scraper.log"
echo ""
echo "💡 İpuçları:"
echo "   - Sistem arkaplanda çalışır"
echo "   - Her 5 dakikada bir kategori değişir"
echo "   - Cache dosyaları scraping_cache/ klasöründe"
echo "   - Monitor'de canlı durumu izleyebilirsiniz"
echo ""
echo "🏠 Evdeki başka bilgisayarlarda da aynı scripti çalıştırabilirsiniz!"
echo "======================================" 