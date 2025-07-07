import os
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Simple HTML template for the main page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>eBay Dropshipping Tool</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .search-box {
            margin: 20px 0;
        }
        input[type="text"] {
            width: 70%;
            padding: 10px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
            background-color: #0064d2;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0052a3;
        }
        .info {
            margin-top: 30px;
            padding: 20px;
            background-color: #f0f8ff;
            border-radius: 5px;
        }
        .api-section {
            margin-top: 30px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        .endpoint {
            background-color: #e8e8e8;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛍️ eBay Dropshipping Tool</h1>
        
        <div class="search-box">
            <form action="/search" method="POST">
                <input type="text" name="keyword" placeholder="Enter product keyword..." required>
                <button type="submit">Search eBay</button>
            </form>
        </div>
        
        <div class="info">
            <h2>Welcome to eBay Dropshipping Tool</h2>
            <p>This application helps you find profitable products on eBay for dropshipping.</p>
            <p><strong>How to use:</strong></p>
            <ul>
                <li>Enter a product keyword in the search box</li>
                <li>Click "Search eBay" to find products</li>
                <li>View product details and pricing information</li>
            </ul>
        </div>
        
        <div class="api-section">
            <h3>API Endpoints for eBay Developer Program</h3>
            <p>Use these endpoints for your eBay application:</p>
            <div class="endpoint">GET /api/health</div>
            <div class="endpoint">POST /api/search</div>
            <div class="endpoint">GET /api/products</div>
            <div class="endpoint">GET /api/webhook</div>
        </div>
    </div>
</body>
</html>
"""

RESULTS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Search Results - eBay Dropshipping</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #0064d2;
            text-decoration: none;
        }
        .product {
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .product h3 {
            margin: 0 0 10px 0;
            color: #0064d2;
        }
        .price {
            font-size: 20px;
            font-weight: bold;
            color: #28a745;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Search</a>
        <h1>Search Results for "{{ keyword }}"</h1>
        
        <div class="results">
            {% for product in products %}
            <div class="product">
                <h3>{{ product.title }}</h3>
                <p class="price">${{ product.price }}</p>
                <p>Condition: {{ product.condition }}</p>
                <p>Seller: {{ product.seller }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Home page with search form"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/search', methods=['POST'])
def search():
    """Handle search requests"""
    keyword = request.form.get('keyword', '')
    
    # Mock data for demonstration
    # In a real app, this would call eBay API
    mock_products = [
        {
            'title': f'{keyword} - Premium Quality Item',
            'price': '29.99',
            'condition': 'Brand New',
            'seller': 'TopSeller123'
        },
        {
            'title': f'{keyword} - Best Value Deal',
            'price': '19.99',
            'condition': 'Like New',
            'seller': 'ValueDeals'
        },
        {
            'title': f'{keyword} - Fast Shipping',
            'price': '34.99',
            'condition': 'New',
            'seller': 'QuickShip'
        }
    ]
    
    return render_template_string(RESULTS_TEMPLATE, keyword=keyword, products=mock_products)

# API endpoints for eBay Developer Program
@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'eBay Dropshipping Tool',
        'version': '1.0.0'
    })

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for searching products"""
    data = request.get_json()
    keyword = data.get('keyword', '')
    
    return jsonify({
        'keyword': keyword,
        'results': [
            {
                'id': '123',
                'title': f'{keyword} Product',
                'price': 29.99,
                'url': 'https://ebay.com/item/123'
            }
        ]
    })

@app.route('/api/products')
def api_products():
    """API endpoint for listing products"""
    return jsonify({
        'products': [
            {'id': '1', 'name': 'Product 1', 'price': 19.99},
            {'id': '2', 'name': 'Product 2', 'price': 29.99}
        ]
    })

@app.route('/api/webhook', methods=['GET', 'POST'])
def webhook():
    """Webhook endpoint for eBay notifications"""
    if request.method == 'GET':
        # eBay webhook verification
        challenge = request.args.get('challenge', '')
        return challenge
    
    # Handle POST webhook data
    return jsonify({'status': 'received'})

@app.route('/privacy')
def privacy():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Privacy Policy - eBay Dropshipping Tool</title>
        <style>body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; background: #f5f5f5; } .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); } h1 { color: #333; } </style>
    </head>
    <body>
        <div class="container">
            <h1>Privacy Policy</h1>
            <p>Your privacy is important to us. This app does not store, share, or sell any personal information. All data is used solely for the purpose of eBay dropshipping product search and is not retained after your session ends.</p>
            <p>If you have any questions, please contact us via the support form.</p>
        </div>
    </body>
    </html>
    """)

@app.route('/auth/success')
def auth_success():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Success - eBay Dropshipping Tool</title>
        <style>body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; background: #f5f5f5; } .container { background: #e6ffe6; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); } h1 { color: #28a745; } </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Authentication Successful</h1>
            <p>You have successfully authenticated with eBay. You may now use the dropshipping tool.</p>
            <a href="/">Go to Home</a>
        </div>
    </body>
    </html>
    """)

@app.route('/auth/failure')
def auth_failure():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Failed - eBay Dropshipping Tool</title>
        <style>body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; background: #f5f5f5; } .container { background: #ffe6e6; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); } h1 { color: #dc3545; } </style>
    </head>
    <body>
        <div class="container">
            <h1>❌ Authentication Failed</h1>
            <p>There was a problem authenticating with eBay. Please try again or contact support if the issue persists.</p>
            <a href="/">Return to Home</a>
        </div>
    </body>
    </html>
    """)

@app.route('/about')
def about():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>About - eBay Dropshipping Tool</title>
        <style>body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px; background: #f5f5f5; } .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); } h1 { color: #333; } .info { margin-top: 20px; }</style>
    </head>
    <body>
        <div class="container">
            <h1>About This App</h1>
            <div class="info">
                <p><strong>eBay Dropshipping Tool</strong> is a simple web application designed to help users find profitable products on eBay for dropshipping.</p>
                <ul>
                    <li>🔍 Search for products by keyword</li>
                    <li>📦 View product details and pricing</li>
                    <li>🔗 Integrate with eBay Developer APIs</li>
                    <li>⚡ Fast, easy, and privacy-friendly</li>
                </ul>
                <p>This app is open source and designed for demonstration and integration with the eBay Developer Program.</p>
                <p>For questions or support, please use the contact form or open an issue on GitHub.</p>
            </div>
            <a href="/">← Back to Home</a>
        </div>
    </body>
    </html>
    """)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 