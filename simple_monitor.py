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

# Basit HTML template
MONITOR_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🖥️ Scraping Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0c1445 0%, #1a237e 100%);
            color: #fff;
            font-family: 'Segoe UI', sans-serif;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        .platform-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .platform-title { font-size: 1.5em; font-weight: bold; }
        .status-dot {
            width: 12px; height: 12px; border-radius: 50%;
            background: #ff4444; animation: pulse 2s infinite;
        }
        .status-dot.active { background: #00ff00; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .metric {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .metric-value { font-size: 2em; font-weight: bold; color: #00ff00; margin-bottom: 5px; }
        .metric-label { font-size: 0.9em; opacity: 0.8; }
        .logs {
            background: rgba(0,0,0,0.4);
            border-radius: 10px;
            padding: 15px;
            height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
        }
        .log-entry { margin-bottom: 5px; padding: 2px 0; }
        .log-info { color: #00ff00; }
        .log-error { color: #ff4444; }
        .system-stats { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; }
        @media (max-width: 768px) {
            .status-grid { grid-template-columns: 1fr; }
            .metrics { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ Scraping Monitor</h1>
            <p>eBay ve Amazon scraping işlemlerini canlı izleyin</p>
        </div>
        
        <div class="status-grid">
            <!-- eBay Card -->
            <div class="card">
                <div class="platform-header">
                    <div class="platform-title">📦 eBay</div>
                    <div id="ebay-status" class="status-dot"></div>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <div id="ebay-items" class="metric-value">0</div>
                        <div class="metric-label">Ürün Bulundu</div>
                    </div>
                    <div class="metric">
                        <div id="ebay-time" class="metric-value">--:--</div>
                        <div class="metric-label">Son Güncelleme</div>
                    </div>
                </div>
                <div class="logs" id="ebay-logs">
                    <div class="log-entry log-info">[{{ current_time }}] Monitor aktif</div>
                </div>
            </div>
            
            <!-- Amazon Card -->
            <div class="card">
                <div class="platform-header">
                    <div class="platform-title">🛒 Amazon</div>
                    <div id="amazon-status" class="status-dot"></div>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <div id="amazon-items" class="metric-value">0</div>
                        <div class="metric-label">Ürün Bulundu</div>
                    </div>
                    <div class="metric">
                        <div id="amazon-time" class="metric-value">--:--</div>
                        <div class="metric-label">Son Güncelleme</div>
                    </div>
                </div>
                <div class="logs" id="amazon-logs">
                    <div class="log-entry log-info">[{{ current_time }}] Monitor aktif</div>
                </div>
            </div>
        </div>
        
        <!-- System Stats -->
        <div class="system-stats">
            <h3>📊 Sistem İstatistikleri</h3>
            <div class="metrics">
                <div class="metric">
                    <div id="cache-files" class="metric-value">{{ cache_count }}</div>
                    <div class="metric-label">Cache Dosyaları</div>
                </div>
                <div class="metric">
                    <div id="uptime" class="metric-value">{{ current_time }}</div>
                    <div class="metric-label">Başlatma Zamanı</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let updateInterval;
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update eBay
                    document.getElementById('ebay-items').textContent = data.ebay_items || 0;
                    document.getElementById('ebay-time').textContent = data.ebay_time || '--:--';
                    
                    // Update Amazon
                    document.getElementById('amazon-items').textContent = data.amazon_items || 0;
                    document.getElementById('amazon-time').textContent = data.amazon_time || '--:--';
                    
                    // Update cache count
                    document.getElementById('cache-files').textContent = data.cache_files || 0;
                })
                .catch(error => {
                    console.log('Status update failed:', error);
                });
        }
        
        // Başlangıç güncelleme
        updateStatus();
        
        // 5 saniyede bir güncelle
        updateInterval = setInterval(updateStatus, 5000);
        
        // Sayfa kapatılırken interval'i temizle
        window.addEventListener('beforeunload', () => {
            if (updateInterval) clearInterval(updateInterval);
        });
    </script>
</body>
</html>
"""

# Global status
monitor_status = {
    "ebay_items": 0,
    "ebay_time": "--:--",
    "amazon_items": 0,
    "amazon_time": "--:--",
    "cache_files": 0,
    "start_time": datetime.now().strftime("%H:%M:%S")
}

@app.route('/')
def index():
    """Ana monitor sayfası"""
    try:
        # Cache dosyalarını say
        cache_dir = "scraping_cache"
        cache_count = 0
        if os.path.exists(cache_dir):
            cache_count = len([f for f in os.listdir(cache_dir) if f.endswith('.json')])
        
        current_time = datetime.now().strftime("%H:%M:%S")
        
        return render_template_string(MONITOR_HTML, 
                                    current_time=current_time,
                                    cache_count=cache_count)
    except Exception as e:
        logger.error(f"Error rendering monitor: {e}")
        return f"Monitor Error: {e}", 500

@app.route('/api/status')
def get_status():
    """Basit status API"""
    try:
        # Cache dosyalarını say
        cache_dir = "scraping_cache"
        cache_count = 0
        if os.path.exists(cache_dir):
            cache_count = len([f for f in os.listdir(cache_dir) if f.endswith('.json')])
        
        monitor_status["cache_files"] = cache_count
        monitor_status["current_time"] = datetime.now().strftime("%H:%M:%S")
        
        return jsonify(monitor_status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/update', methods=['POST'])
def update_status():
    """Status güncelleme endpoint'i"""
    try:
        from flask import request
        data = request.get_json()
        if data:
            monitor_status.update(data)
            return jsonify({"status": "ok"})
        return jsonify({"error": "No data"}), 400
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🖥️  Simple Scraping Monitor starting...")
    print("📊 Dashboard: http://localhost:8082")
    print("🔄 Use Ctrl+C to stop")
    
    # Minimal Flask app - hızlı başlatma
    app.run(debug=False, host='0.0.0.0', port=8082, threaded=True) 