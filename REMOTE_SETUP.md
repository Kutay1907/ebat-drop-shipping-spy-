# 🌐 Uzak Sunucu Kurulum Rehberi

Bu rehber, eBay Dropshipping Spy sistemini uzak bir sunucuda veya başka bir bilgisayarda kurmanız için hazırlanmıştır.

## 🎯 Seçenekler

### 1. Evdeki Başka Bir Bilgisayar
- **Avantajlar**: Ücretsiz, tam kontrol, hızlı internet
- **Dezavantajlar**: Sürekli açık tutmalısınız, elektrik maliyeti

### 2. VPS (Virtual Private Server)
- **Önerilen**: DigitalOcean, Linode, Vultr
- **Maliyet**: $5-20/ay
- **Avantajlar**: 7/24 çalışır, profesyonel

### 3. Raspberry Pi
- **Maliyet**: ~$100 (bir kerelik)
- **Avantajlar**: Düşük elektrik tüketimi, sessiz

## 🚀 Kurulum Adımları

### A. Ubuntu/Debian Sunucu Kurulumu

```bash
# 1. Sistemi güncelleyin
sudo apt update && sudo apt upgrade -y

# 2. Python ve gerekli paketleri yükleyin
sudo apt install python3 python3-pip python3-venv git -y

# 3. Playwright için gerekli paketler
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libgbm1 \
    libasound2

# 4. Projeyi klonlayın
git clone https://github.com/your-repo/ebay-dropshipping-spy.git
cd ebay-dropshipping-spy

# 5. Virtual environment oluşturun
python3 -m venv venv
source venv/bin/activate

# 6. Gerekli paketleri yükleyin
pip install -r requirements.txt

# 7. Playwright browserları yükleyin
playwright install
```

### B. Systemd Servisi Oluşturma (Ubuntu/Debian)

```bash
# Servis dosyası oluşturun
sudo nano /etc/systemd/system/ebay-scraper.service
```

Aşağıdaki içeriği ekleyin:

```ini
[Unit]
Description=eBay Dropshipping Background Scraper
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ebay-dropshipping-spy
Environment=PATH=/home/ubuntu/ebay-dropshipping-spy/venv/bin
ExecStart=/home/ubuntu/ebay-dropshipping-spy/venv/bin/python background_scraper.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Servisi başlatın:

```bash
# Servisi etkinleştirin
sudo systemctl enable ebay-scraper.service

# Servisi başlatın
sudo systemctl start ebay-scraper.service

# Durumu kontrol edin
sudo systemctl status ebay-scraper.service

# Logları görüntüleyin
sudo journalctl -u ebay-scraper.service -f
```

### C. Web Arayüzü için Nginx (Opsiyonel)

```bash
# Nginx yükleyin
sudo apt install nginx -y

# Konfigürasyon dosyası oluşturun
sudo nano /etc/nginx/sites-available/ebay-scraper
```

Nginx konfigürasyonu:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Veya IP adresiniz

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /monitor {
        proxy_pass http://127.0.0.1:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Nginx'i etkinleştirin:

```bash
sudo ln -s /etc/nginx/sites-available/ebay-scraper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔧 Yapılandırma

### Proxy Kullanımı (Önerilen)

```python
# real_ebay_scraper.py ve real_amazon_scraper.py'de proxy ayarları
PROXY_LIST = [
    "http://username:password@proxy1.com:8080",
    "http://username:password@proxy2.com:8080",
    # Daha fazla proxy ekleyin
]
```

### Rate Limiting Ayarları

```python
# background_scraper.py'de bekleme sürelerini artırın
await asyncio.sleep(10)  # Istekler arası bekleme
self.scrape_interval = 7200  # 2 saat (daha az sıklık)
```

## 📊 İzleme ve Yönetim

### 1. Cron Job ile Otomatik Yeniden Başlatma

```bash
# Crontab düzenleyin
crontab -e

# Her gün 03:00'da yeniden başlat
0 3 * * * sudo systemctl restart ebay-scraper.service
```

### 2. Log Rotasyonu

```bash
# Logrotate konfigürasyonu
sudo nano /etc/logrotate.d/ebay-scraper
```

```
/home/ubuntu/ebay-dropshipping-spy/background_scraper.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ubuntu ubuntu
}
```

### 3. Monitoring Script

```bash
#!/bin/bash
# monitor.sh - Scraper durumunu kontrol et

LOG_FILE="/home/ubuntu/ebay-dropshipping-spy/background_scraper.log"
LAST_ACTIVITY=$(tail -n 100 "$LOG_FILE" | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}' | tail -1)

if [ -z "$LAST_ACTIVITY" ]; then
    echo "❌ Log dosyasında aktivite bulunamadı"
    exit 1
fi

LAST_TIMESTAMP=$(date -d "$LAST_ACTIVITY" +%s)
CURRENT_TIMESTAMP=$(date +%s)
DIFF=$((CURRENT_TIMESTAMP - LAST_TIMESTAMP))

# 30 dakikadan fazla aktivite yoksa uyarı
if [ $DIFF -gt 1800 ]; then
    echo "⚠️  Son aktivite: $LAST_ACTIVITY (${DIFF} saniye önce)"
    echo "🔄 Servis yeniden başlatılıyor..."
    sudo systemctl restart ebay-scraper.service
else
    echo "✅ Scraper aktif - Son aktivite: $LAST_ACTIVITY"
fi
```

## 🌍 Önerilen VPS Sağlayıcıları

### 1. DigitalOcean
- **Fiyat**: $6/ay (1GB RAM)
- **Avantajlar**: Kolay kurulum, iyi dokümantasyon
- **Link**: https://digitalocean.com

### 2. Vultr
- **Fiyat**: $5/ay (1GB RAM)
- **Avantajlar**: Hızlı SSD, çok lokasyon
- **Link**: https://vultr.com

### 3. Linode
- **Fiyat**: $5/ay (1GB RAM)
- **Avantajlar**: Stabil, güvenilir
- **Link**: https://linode.com

## 🔐 Güvenlik Önerileri

### 1. SSH Key Kullanımı
```bash
# SSH key oluşturun (yerel bilgisayarınızda)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Public key'i sunucuya kopyalayın
ssh-copy-id username@server-ip
```

### 2. Firewall Ayarları
```bash
# UFW firewall'u etkinleştirin
sudo ufw enable

# Sadece gerekli portları açın
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

### 3. Otomatik Güncellemeler
```bash
# Unattended upgrades yükleyin
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 📞 Destek ve Sorun Giderme

### Yaygın Sorunlar:

1. **Browser çalışmıyor**: `playwright install` komutunu çalıştırın
2. **Permission denied**: Dosya izinlerini kontrol edin
3. **Memory hatası**: Daha fazla RAM'e sahip sunucu seçin
4. **Network timeout**: Proxy kullanmayı deneyin

### Log Dosyalarını Kontrol Etme:
```bash
# Background scraper logları
tail -f background_scraper.log

# System service logları
sudo journalctl -u ebay-scraper.service -f

# Web app logları
tail -f logs/web_app.log
```

## 🎯 Sonuç

Bu kurulum ile:
- ✅ 7/24 otomatik scraping
- ✅ Web arayüzü erişimi
- ✅ Otomatik yeniden başlatma
- ✅ Log izleme
- ✅ Güvenli erişim

Kurulum tamamlandıktan sonra web arayüzüne `http://your-server-ip` adresinden erişebilirsiniz. 