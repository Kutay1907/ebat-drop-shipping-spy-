#!/bin/bash

# eBay Dropshipping Spy - Background Scraper Starter
# macOS için arkaplan scraper başlatıcı

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 eBay Background Scraper Başlatılıyor..."
echo "📁 Çalışma dizini: $SCRIPT_DIR"

# Python sanal ortamını kontrol et
if [ -d "venv" ]; then
    echo "🐍 Virtual environment bulundu, aktifleştiriliyor..."
    source venv/bin/activate
fi

# Gerekli dosyaları kontrol et
if [ ! -f "background_scraper.py" ]; then
    echo "❌ background_scraper.py bulunamadı!"
    exit 1
fi

# PID dosyası
PID_FILE="$SCRIPT_DIR/background_scraper.pid"

# Zaten çalışıyor mu kontrol et
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Background scraper zaten çalışıyor (PID: $OLD_PID)"
        echo "Durdurmak için: kill $OLD_PID"
        exit 1
    else
        echo "🧹 Eski PID dosyası temizleniyor..."
        rm "$PID_FILE"
    fi
fi

# Log klasörü oluştur
mkdir -p logs

# Background scraper'ı başlat
echo "🔄 Background scraper başlatılıyor..."
nohup python3 background_scraper.py > logs/background_scraper_output.log 2>&1 &
SCRAPER_PID=$!

# PID'i kaydet
echo $SCRAPER_PID > "$PID_FILE"

echo "✅ Background scraper başlatıldı!"
echo "📊 PID: $SCRAPER_PID"
echo "📝 Log dosyası: background_scraper.log"
echo "📄 Output log: logs/background_scraper_output.log"
echo ""
echo "Durumu kontrol etmek için:"
echo "  tail -f background_scraper.log"
echo ""
echo "Durdurmak için:"
echo "  kill $SCRAPER_PID"
echo "  veya"
echo "  ./stop_background.sh"
echo ""
echo "Web arayüzünü başlatmak için:"
echo "  python web_app.py" 