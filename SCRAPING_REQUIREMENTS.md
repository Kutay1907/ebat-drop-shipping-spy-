# 🔍 eBay & Amazon Scraping Gereksinimleri

## 🖥️ Sistem Gereksinimleri

### 1. **VPS/Sunucu Gereksinimleri**
- **Minimum:** 2 vCPU, 4GB RAM, 20GB SSD
- **Önerilen:** 4 vCPU, 8GB RAM, 50GB SSD
- **İşletim Sistemi:** Ubuntu 20.04+ veya Windows Server 2019+
- **Önerilen VPS Sağlayıcıları:**
  - DigitalOcean ($24/ay başlangıç)
  - Vultr ($20/ay başlangıç)
  - Hetzner (€5/ay başlangıç - en ucuz)
  - AWS EC2 (t3.medium instance)

### 2. **Proxy Gereksinimleri**

#### Residential Proxy (Önerilen)
- **Bright Data:** $500/ay (10GB) - En kaliteli
- **Smartproxy:** $75/ay (5GB) - Uygun fiyatlı
- **Oxylabs:** $300/ay (20GB) - Kurumsal
- **IPRoyal:** $7/GB - Kullandıkça öde

#### Datacenter Proxy (Bütçe Dostu)
- **Webshare:** $30/ay (10 proxy)
- **ProxyMesh:** $10/ay (10 proxy)
- **Storm Proxies:** $50/ay (40 proxy)

### 3. **Captcha Çözüm Servisleri**
- **2Captcha:** $3/1000 captcha
- **Anti-Captcha:** $2/1000 captcha
- **DeathByCaptcha:** $1.4/1000 captcha

## 🛠️ Kurulum Adımları

### 1. VPS Kurulumu
```bash
# Ubuntu için
sudo apt update && sudo apt upgrade -y
sudo apt install python3.10 python3-pip git -y

# Playwright için gerekli kütüphaneler
sudo apt install libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libgtk-3-0 -y
```

### 2. Proxy Yapılandırması
```python
# proxy_config.py oluşturun
PROXY_CONFIG = {
    "server": "http://proxy-server.com:8080",
    "username": "your-username",
    "password": "your-password"
}
```

### 3. Anti-Bot Önlemleri
```python
# Playwright stealth ayarları
context = await browser.new_context(
    viewport={'width': 1920, 'height': 1080},
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    locale='en-US',
    timezone_id='America/New_York',
    proxy={
        "server": "http://proxy:8080",
        "username": "user",
        "password": "pass"
    }
)
```

## 💰 Maliyet Hesaplama

### Aylık Tahmini Maliyetler:
- **VPS:** $20-50
- **Proxy:** $30-100 (kullanıma göre)
- **Captcha:** $10-30 (kullanıma göre)
- **Toplam:** $60-180/ay

### Günlük Scraping Limitleri:
- **Proxy olmadan:** 50-100 ürün/gün
- **Datacenter proxy:** 500-1000 ürün/gün
- **Residential proxy:** 5000-10000 ürün/gün

## 🚀 Performans İpuçları

### 1. Rate Limiting
```python
# Her istek arasında rastgele bekleme
await asyncio.sleep(random.uniform(2, 5))
```

### 2. Session Rotation
```python
# Her 50 üründe bir yeni browser session
if product_count % 50 == 0:
    await browser.close()
    browser = await playwright.chromium.launch()
```

### 3. User-Agent Rotation
```python
from fake_useragent import UserAgent
ua = UserAgent()
user_agent = ua.random
```

## 🔒 Güvenlik Önlemleri

1. **IP Rotation:** Her 10-20 istekte bir proxy değiştir
2. **Fingerprint Masking:** Canvas, WebGL, fonts vb. değiştir
3. **Cookie Management:** Session cookie'lerini sakla ve kullan
4. **Request Headers:** Gerçekçi header'lar kullan
5. **JavaScript Execution:** Sayfada normal kullanıcı gibi davran

## 📊 Monitoring ve Logging

1. **Scraping Monitor:** http://localhost:8082
2. **Log Dosyaları:** `/var/log/scraping/`
3. **Hata Takibi:** Sentry veya Rollbar kullan
4. **Metrikler:** Prometheus + Grafana

## 🆘 Sorun Giderme

### Sık Karşılaşılan Hatalar:
1. **"Access Denied":** Proxy değiştir
2. **"Too Many Requests":** Rate limit azalt
3. **"Browser Closed":** Memory leak kontrol et
4. **"Captcha":** Captcha servisi kullan

### Debug Modu:
```bash
# Headless kapatarak debug yap
python web_app.py --debug --no-headless
```

## 📞 Destek

Sorularınız için:
- GitHub Issues: [Proje Sayfası]
- Email: support@example.com
- Discord: [Topluluk Sunucusu] 