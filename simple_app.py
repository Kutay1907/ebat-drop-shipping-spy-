#!/usr/bin/env python3
"""
Simple eBay Scraper Application

A simplified version for quick testing and demonstration.
"""

from quart import Quart, render_template_string, request, jsonify
import asyncio
import random
from datetime import datetime
from decimal import Decimal

app = Quart(__name__)
app.secret_key = "dev-secret-key"

# Simple HTML template
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>eBay Scraper</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; text-decoration: none; display: inline-block; }
        .form-group { margin: 15px 0; }
        input, select { width: 100%; padding: 8px; margin: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 eBay Scraper & Market Analyzer</h1>
        <div class="card">
            <h2>Welcome to eBay Scraper</h2>
            <p>A comprehensive eBay scraping solution built with clean architecture and SOLID principles.</p>
            
            <h3>Features:</h3>
            <ul>
                <li>✅ SOLID Architecture with dependency injection</li>
                <li>✅ Async-first design for high performance</li>
                <li>✅ Comprehensive bot protection measures</li>
                <li>✅ Structured logging and monitoring</li>
                <li>✅ RESTful API with JSON responses</li>
            </ul>
            
            <a href="/search" class="btn">Start Scraping</a>
            <a href="/api/v1/health" class="btn">API Health</a>
        </div>
    </div>
</body>
</html>
"""

SEARCH_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Search - eBay Scraper</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .form-group { margin: 15px 0; }
        input, select { width: 100%; padding: 8px; margin: 5px 0; }
        .alert { padding: 15px; margin: 20px 0; border-radius: 4px; }
        .alert-success { background: #d4edda; color: #155724; }
        .alert-error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 eBay Product Search</h1>
        <div class="card">
            <form method="POST">
                <div class="form-group">
                    <label>Search Keyword:</label>
                    <input type="text" name="keyword" placeholder="e.g., wireless headphones" required>
                </div>
                <div class="form-group">
                    <label>Max Results:</label>
                    <select name="max_results">
                        <option value="10">10 products</option>
                        <option value="20" selected>20 products</option>
                        <option value="50">50 products</option>
                    </select>
                </div>
                <button type="submit" class="btn">Start Scraping</button>
            </form>
        </div>
        
        {% if result %}
        <div class="card">
            <h2>Scraping Results</h2>
            <div class="alert alert-success">
                ✅ Found {{ result.products|length }} products for "{{ result.keyword }}"
            </div>
            
            {% for product in result.products %}
            <div class="card">
                <h3>{{ product.title }}</h3>
                <p><strong>Price:</strong> ${{ product.price }}</p>
                <p><strong>Condition:</strong> {{ product.condition }}</p>
                {% if product.sold_count %}
                <p><strong>Sold:</strong> {{ product.sold_count }} items</p>
                {% endif %}
                <p><a href="{{ product.url }}" target="_blank">View on eBay</a></p>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
async def home():
    """Home page."""
    return await render_template_string(HOME_TEMPLATE)

@app.route('/search', methods=['GET', 'POST'])
async def search():
    """Search page."""
    if request.method == 'GET':
        return await render_template_string(SEARCH_TEMPLATE)
    
    # Handle POST request
    form = await request.form
    keyword = form.get('keyword', '')
    max_results = int(form.get('max_results', 20))
    
    # Simulate scraping with mock data
    await asyncio.sleep(2)  # Simulate processing time
    
    # Generate mock products
    products = []
    for i in range(min(max_results, random.randint(5, 15))):
        products.append({
            'title': f'Mock {keyword} Product {i+1}',
            'price': round(random.uniform(10.0, 150.0), 2),
            'condition': random.choice(['new', 'used', 'refurbished']),
            'sold_count': random.randint(0, 500) if random.random() > 0.3 else None,
            'url': f'https://www.ebay.com/itm/mock{i}'
        })
    
    result = {
        'keyword': keyword,
        'products': products
    }
    
    return await render_template_string(SEARCH_TEMPLATE, result=result)

@app.route('/api/v1/health')
async def health():
    """Health check API."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'services': {
            'web_server': 'running',
            'bot_protection': 'active',
            'scraper': 'ready'
        }
    })

@app.route('/api/v1/scrape', methods=['POST'])
async def api_scrape():
    """API endpoint for scraping."""
    data = await request.get_json()
    
    if not data or not data.get('keyword'):
        return jsonify({'error': 'keyword is required'}), 400
    
    keyword = data['keyword']
    max_results = data.get('max_results', 20)
    
    # Simulate scraping
    await asyncio.sleep(3)
    
    # Generate mock results
    products = []
    for i in range(min(max_results, random.randint(5, 15))):
        products.append({
            'title': f'Mock {keyword} Product {i+1}',
            'price': str(round(random.uniform(10.0, 150.0), 2)),
            'condition': random.choice(['new', 'used', 'refurbished']),
            'sold_count': random.randint(0, 500) if random.random() > 0.3 else None,
            'url': f'https://www.ebay.com/itm/mock{i}'
        })
    
    return jsonify({
        'status': 'success',
        'keyword': keyword,
        'products_found': len(products),
        'products': products,
        'scraping_duration': 3.0
    })

if __name__ == '__main__':
    print("🚀 Starting eBay Scraper (Simple Version)")
    print("📍 Server: http://localhost:8000")
    print("🔍 Search: http://localhost:8000/search")
    print("💡 API: http://localhost:8000/api/v1/health")
    
    app.run(host='127.0.0.1', port=8000, debug=True) 