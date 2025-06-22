#!/bin/bash

# eBay Dropshipping Spy - Background Scraper Stopper
# Arkaplan scraper'ı durdurmak için

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/background_scraper.pid"

echo "🛑 Background Scraper Durduruluyor..."

if [ ! -f "$PID_FILE" ]; then
    echo "❌ PID dosyası bulunamadı. Scraper çalışmıyor olabilir."
    exit 1
fi

SCRAPER_PID=$(cat "$PID_FILE")

if ps -p "$SCRAPER_PID" > /dev/null 2>&1; then
    echo "🔄 Scraper durduruluyor (PID: $SCRAPER_PID)..."
    kill "$SCRAPER_PID"
    
    # 5 saniye bekle
    sleep 5
    
    # Hala çalışıyor mu kontrol et
    if ps -p "$SCRAPER_PID" > /dev/null 2>&1; then
        echo "⚠️  Normal durdurma başarısız, zorla durduruluyor..."
        kill -9 "$SCRAPER_PID"
        sleep 2
    fi
    
    # Son kontrol
    if ps -p "$SCRAPER_PID" > /dev/null 2>&1; then
        echo "❌ Scraper durdurulamadı!"
        exit 1
    else
        echo "✅ Scraper başarıyla durduruldu!"
    fi
else
    echo "⚠️  Scraper zaten durdurulmuş."
fi

# PID dosyasını temizle
rm -f "$PID_FILE"

echo "🧹 PID dosyası temizlendi."
echo ""
echo "Log dosyalarını görmek için:"
echo "  tail background_scraper.log"
echo "  tail logs/background_scraper_output.log" 