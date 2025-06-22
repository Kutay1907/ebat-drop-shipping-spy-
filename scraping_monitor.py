#!/usr/bin/env python3
"""
Scraping Monitor - eBay ve Amazon scraping işlemlerini görselleştiren web arayüzü
Port: 8082
"""

import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_cors import CORS
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global scraping status - simplified and optimized
scraping_status = {
    "ebay": {
        "active": False,
        "current_url": "",
        "items_found": 0,
        "last_update": "",
        "logs": [],
        "category": "",
        "progress": 0
    },
    "amazon": {
        "active": False,
        "current_url": "",
        "items_found": 0,
        "last_update": "",
        "logs": [],
        "search_term": "",
        "progress": 0
    },
    "system": {
        "total_products": 0,
        "total_matches": 0,
        "uptime": datetime.now().strftime("%H:%M:%S")
    }
}

# Cache directory
CACHE_DIR = "scraping_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def update_status(platform, **kwargs):
    """Update scraping status with error handling"""
    try:
        global scraping_status
        if platform in scraping_status:
            scraping_status[platform].update(kwargs)
            scraping_status[platform]["last_update"] = datetime.now().strftime("%H:%M:%S")
            logger.info(f"Status updated for {platform}: {kwargs}")
    except Exception as e:
        logger.error(f"Error updating status for {platform}: {e}")

def add_log(platform, message, level="info"):
    """Add log message with size limit"""
    try:
        global scraping_status
        if platform in scraping_status:
            log_entry = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "message": str(message)[:200],  # Limit message length
                "level": level
            }
            scraping_status[platform]["logs"].append(log_entry)
            # Keep only last 20 logs for better performance
            if len(scraping_status[platform]["logs"]) > 20:
                scraping_status[platform]["logs"] = scraping_status[platform]["logs"][-20:]
    except Exception as e:
        logger.error(f"Error adding log for {platform}: {e}")

@app.route('/')
def index():
    """Monitor dashboard"""
    try:
        return render_template('monitor.html')
    except Exception as e:
        logger.error(f"Error rendering monitor.html: {e}")
        return f"Monitor Error: {e}", 500

@app.route('/api/status')
def get_status():
    """Get current scraping status - optimized"""
    try:
        # Update system stats
        cache_files = len([f for f in os.listdir(CACHE_DIR) if f.endswith('.json')])
        scraping_status["system"]["cache_files"] = cache_files
        
        return jsonify(scraping_status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/log/<platform>', methods=['POST'])
def add_log_endpoint(platform):
    """Add log message via API"""
    try:
        data = request.get_json()
        if data and platform in scraping_status:
            add_log(platform, data.get('message', ''), data.get('level', 'info'))
            return jsonify({"status": "ok"})
        return jsonify({"error": "Invalid data"}), 400
    except Exception as e:
        logger.error(f"Error in log endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/update/<platform>', methods=['POST'])
def update_status_endpoint(platform):
    """Update status via API"""
    try:
        data = request.get_json()
        if data and platform in scraping_status:
            update_status(platform, **data)
            return jsonify({"status": "ok"})
        return jsonify({"error": "Invalid data"}), 400
    except Exception as e:
        logger.error(f"Error in update endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cache')
def get_cache_summary():
    """Get cache summary"""
    try:
        cache_files = []
        if os.path.exists(CACHE_DIR):
            for filename in os.listdir(CACHE_DIR):
                if filename.endswith('.json'):
                    filepath = os.path.join(CACHE_DIR, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            cache_files.append({
                                "filename": filename,
                                "products": len(data.get('products', [])),
                                "timestamp": data.get('timestamp', ''),
                                "category": data.get('category_name', filename)
                            })
                    except:
                        continue
        
        return jsonify({"cache_files": cache_files})
    except Exception as e:
        logger.error(f"Error getting cache summary: {e}")
        return jsonify({"error": str(e)}), 500

# Initialize with some demo logs
add_log("ebay", "Monitor başlatıldı", "info")
add_log("amazon", "Monitor başlatıldı", "info")

if __name__ == '__main__':
    print("🖥️  Scraping Monitor starting...")
    print("📊 Dashboard: http://localhost:8082")
    print("🔄 Use Ctrl+C to stop")
    
    # Disable Flask debug for better performance
    app.run(debug=False, host='0.0.0.0', port=8082, threaded=True) 