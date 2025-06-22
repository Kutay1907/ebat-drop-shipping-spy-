# 🚀 eBay Dropshipping Spy

eBay ve Amazon arasında karlı dropshipping fırsatlarını otomatik olarak bulan ve analiz eden Python uygulaması.

## 🎯 Özellikler

- ✅ **Gerçek Zamanlı Scraping**: eBay ve Amazon'dan canlı veri çekme
- 📊 **Karlılık Analizi**: %50+ kar marjı olan ürünleri bulma
- 🔍 **Akıllı Eşleştirme**: Ürünleri metin ve görsel benzerlikle eşleştirme
- 📈 **Canlı Monitoring**: Scraping işlemlerini gerçek zamanlı izleme
- 🔄 **Arkaplan Çalışma**: Sürekli otomatik veri toplama
- 🌐 **Web Arayüzü**: Kullanıcı dostu Türkçe arayüz
- 💾 **Cache Sistemi**: Verimli veri saklama ve yeniden kullanım

## 📋 Gereksinimler

- Python 3.8+
- Chrome/Chromium browser
- İnternet bağlantısı

## 🛠️ Kurulum

### Windows Kurulumu (Kolay)

1. **Dosyaları İndirin**:
   ```bash
   git clone https://github.com/your-username/ebay-dropshipping-spy.git
   cd ebay-dropshipping-spy
   ```

2. **Kurulum Scriptini Çalıştırın**:
   ```cmd
   setup_windows.bat
   ```

3. **Sistemi Başlatın**:
   ```cmd
   start_windows.bat
   ```

### macOS/Linux Kurulumu

1. **Repository'yi Klonlayın**:
   ```bash
   git clone https://github.com/your-username/ebay-dropshipping-spy.git
   cd ebay-dropshipping-spy
   ```

2. **Gerekli Paketleri Kurun**:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **Sistemi Başlatın**:
   ```bash
   ./start_background.sh
   ```

## 🚀 Kullanım

### 1. Web Arayüzü (Ana Uygulama)
- **URL**: http://localhost:8081
- Kategori seçimi ve analiz başlatma
- Sonuçları görüntüleme ve filtreleme
- Ürün detayları ve karlılık bilgileri

### 2. Monitoring Dashboard
- **URL**: http://localhost:8082
- Canlı scraping durumu
- İstatistikler ve loglar
- Sistem performansı

### 3. Arkaplan Scraper
- Otomatik kategori taraması
- Sürekli veri toplama
- Cache sistemi ile hızlı erişim

## 📊 Özellik Detayları

### Karlılık Kriterleri
- **Minimum Kar Marjı**: %50
- **Minimum Satış Sayısı**: 3+ satış
- **Fiyat Aralığı**: Özelleştirilebilir
- **Kategori Filtresi**: 10+ ana kategori

### Desteklenen Kategoriler
- Consumer Electronics
- Cell Phones & Accessories
- Clothing, Shoes & Accessories
- Computers/Tablets & Networking
- Home & Garden
- Collectibles & Art
- Books, Movies & Music
- Baby Products
- Business & Industrial

### Veri Analizi
- **Metin Benzerliği**: Fuzzy string matching
- **Görsel Eşleştirme**: PIL tabanlı görsel karşılaştırma
- **Fiyat Analizi**: Otomatik kar marjı hesaplama
- **Trend Analizi**: Satış performansı değerlendirmesi

## 🔧 Yapılandırma

### Ayarlar (web_app.py)
```python
SETTINGS = {
    'min_profit': 50.0,      # Minimum kar marjı (%)
    'min_sold_count': 3,     # Minimum satış sayısı
    'max_products': 50,      # Maksimum ürün sayısı
    'cache_duration': 3600,  # Cache süresi (saniye)
}
```

### Scraping Ayarları
- **Timeout**: 60 saniye
- **Retry**: 3 deneme
- **Delay**: 2-5 saniye arası
- **User-Agent**: Rotasyon sistemi

## 📁 Dosya Yapısı

```
ebay-dropshipping-spy/
├── web_app.py              # Ana web uygulaması
├── background_scraper.py   # Arkaplan scraper
├── simple_monitor.py       # Monitoring dashboard
├── real_ebay_scraper.py    # eBay scraper
├── real_amazon_scraper.py  # Amazon scraper
├── matcher.py              # Ürün eşleştirme
├── utils.py                # Yardımcı fonksiyonlar
├── templates/              # HTML şablonları
├── scraping_cache/         # Cache dosyaları
├── setup_windows.bat       # Windows kurulum
├── start_windows.bat       # Windows başlatıcı
├── stop_windows.bat        # Windows durdurucu
└── requirements.txt        # Python bağımlılıkları
```

## 🔒 Güvenlik ve Etik

- **Rate Limiting**: Sitelere aşırı yük bindirmeme
- **User-Agent Rotation**: Bot tespitini önleme
- **Respectful Scraping**: robots.txt'e uygun davranış
- **Legal Compliance**: Sadece halka açık veriler

## ⚠️ Sorun Giderme

### Yaygın Sorunlar

1. **Port Çakışması**:
   ```cmd
   stop_windows.bat
   start_windows.bat
   ```

2. **Browser Hatası**:
   ```bash
   playwright install
   ```

3. **Python Paketi Eksik**:
   ```bash
   pip install -r requirements.txt
   ```

### Log Dosyaları
- `background_scraper.log` - Arkaplan scraper logları
- `scraping_cache/` - Cache ve hata logları

## 📈 Performans

- **Scraping Hızı**: ~50 ürün/dakika
- **Memory Kullanımı**: ~200MB
- **Cache Boyutu**: ~10MB/kategori
- **Response Time**: <2 saniye

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit yapın (`git commit -m 'Add some AmazingFeature'`)
4. Push yapın (`git push origin feature/AmazingFeature`)
5. Pull Request açın

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 📞 İletişim

- **GitHub**: [your-username](https://github.com/your-username)
- **Email**: your-email@example.com

## 🎉 Teşekkürler

- Playwright ekibine browser automation için
- Flask ekibine web framework için
- Açık kaynak topluluğuna katkılarından dolayı

---

⭐ **Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!** ⭐