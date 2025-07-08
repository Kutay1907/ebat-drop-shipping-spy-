from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Revolist API...")
    
    # Validate critical environment variables (but don't fail if missing, just warn)
    env_vars = ["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET", "EBAY_REDIRECT_URI"]
    for var in env_vars:
        if not os.getenv(var):
            logger.warning(f"Environment variable {var} is not set - some features may not work")
    
    try:
        from app.database import init_db
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Don't fail startup - let the app run even if DB fails
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="eBay Dropshipping Spy API",
    description="Professional eBay product research and API integration platform",
    version="2.0.0",
    lifespan=lifespan
)

# Import and register routes
from app.search_routes import router as search_router
from app.auth_routes import router as auth_router

app.include_router(search_router)
app.include_router(auth_router)

# Add a debug endpoint
@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables (don't expose secrets)"""
    env_status = {}
    check_vars = ["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET", "EBAY_REDIRECT_URI", "DATABASE_URL", "PORT"]
    for var in check_vars:
        value = os.getenv(var)
        env_status[var] = "SET" if value else "NOT_SET"
    return {"environment": env_status}

# Enhanced HTML with comprehensive eBay API documentation and modern UI
HTML_HOME = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>eBay Dropshipping Spy - Professional Product Research</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 40px; }
        .header h1 { font-size: 3rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2rem; opacity: 0.9; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; margin-bottom: 40px; }
        .card { background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); transition: transform 0.3s ease; }
        .card:hover { transform: translateY(-5px); }
        .card h3 { color: #333; margin-bottom: 15px; font-size: 1.4rem; }
        .card p { color: #666; margin-bottom: 20px; line-height: 1.6; }
        .btn { display: inline-block; padding: 12px 25px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; transition: background 0.3s ease; border: none; cursor: pointer; }
        .btn:hover { background: #5a6fd8; }
        .btn-secondary { background: #6c757d; }
        .btn-secondary:hover { background: #545b62; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }
        .feature { background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #667eea; }
        .feature h4 { color: #333; margin-bottom: 10px; }
        .feature p { color: #666; font-size: 0.9rem; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
        .status-online { background: #28a745; }
        .status-offline { background: #dc3545; }
        .api-demo { background: #f8f9fa; border-radius: 10px; padding: 25px; margin-top: 30px; }
        .code-block { background: #2d3748; color: #e2e8f0; padding: 20px; border-radius: 8px; font-family: 'Courier New', monospace; font-size: 0.9rem; overflow-x: auto; margin: 15px 0; }
        .endpoint { background: #e8f4fd; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #0066cc; }
        .method-get { background: #d4edda; border-left-color: #28a745; }
        .method-post { background: #fff3cd; border-left-color: #ffc107; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .stat { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; text-align: center; color: white; }
        .stat h3 { font-size: 2rem; margin-bottom: 5px; }
        .stat p { opacity: 0.9; }
        .demo-section { background: white; border-radius: 15px; padding: 30px; margin-top: 30px; }
        .demo-controls { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .demo-input { padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 1rem; width: 100%; }
        .demo-results { background: #f8f9fa; border-radius: 8px; padding: 20px; margin-top: 20px; min-height: 200px; }
        .loading { text-align: center; color: #666; font-style: italic; }
        .tab-container { margin-top: 30px; }
        .tabs { display: flex; background: #f8f9fa; border-radius: 10px 10px 0 0; overflow: hidden; }
        .tab { padding: 15px 25px; background: #e9ecef; border: none; cursor: pointer; font-weight: 600; color: #666; flex: 1; }
        .tab.active { background: white; color: #333; border-bottom: 3px solid #667eea; }
        .tab-content { background: white; padding: 30px; border-radius: 0 0 10px 10px; min-height: 400px; }
        .hidden { display: none; }
        @media (max-width: 768px) {
            .header h1 { font-size: 2rem; }
            .cards { grid-template-columns: 1fr; }
            .demo-controls { grid-template-columns: 1fr; }
            .tabs { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 eBay Dropshipping Spy</h1>
            <p>Professional Product Research & API Integration Platform</p>
            <div class="stats">
                <div class="stat">
                    <h3>∞</h3>
                    <p>API Endpoints</p>
                </div>
                <div class="stat">
                    <h3>10+</h3>
                    <p>Marketplaces</p>
                </div>
                <div class="stat">
                    <h3>24/7</h3>
                    <p>Uptime</p>
                </div>
                <div class="stat">
                    <h3>Real-time</h3>
                    <p>Data</p>
                </div>
            </div>
        </div>

        <div class="cards">
            <div class="card">
                <h3>🚀 Quick Product Search</h3>
                <p>Search millions of eBay products instantly. Get real-time pricing, availability, and seller information for your dropshipping research.</p>
                <button class="btn" onclick="openTab('search')">Start Searching</button>
                <a href="/api/health" class="btn btn-secondary" style="margin-left: 10px;">API Status</a>
            </div>

            <div class="card">
                <h3>⚡ Advanced API Integration</h3>
                <p>Convert any eBay API Explorer call into working Python code. Support for all HTTP methods and eBay endpoints with automatic authentication.</p>
                <button class="btn" onclick="openTab('api')">API Explorer</button>
                <a href="/api/test-connection" class="btn btn-secondary" style="margin-left: 10px;">Test Connection</a>
            </div>

            <div class="card">
                <h3>🔧 Professional Features</h3>
                <p>Advanced filters, multiple marketplaces, rate limiting, error handling, and automatic token management for production use.</p>
                <button class="btn" onclick="openTab('features')">View Features</button>
                <a href="/api/marketplace/info" class="btn btn-secondary" style="margin-left: 10px;">Marketplaces</a>
            </div>
        </div>

        <div class="tab-container">
            <div class="tabs">
                <button class="tab active" onclick="openTab('search')">Product Search</button>
                <button class="tab" onclick="openTab('api')">API Integration</button>
                <button class="tab" onclick="openTab('features')">Advanced Features</button>
                <button class="tab" onclick="openTab('docs')">Documentation</button>
            </div>

            <div id="search" class="tab-content">
                <h3>🔍 eBay Product Search</h3>
                <p>Search millions of eBay products with advanced filtering and real-time data.</p>
                
                <div class="demo-controls">
                    <input type="text" id="searchKeyword" class="demo-input" placeholder="Enter product keyword (e.g., 'wireless headphones')" value="laptop">
                    <select id="marketplace" class="demo-input">
                        <option value="EBAY_US">United States (USD)</option>
                        <option value="EBAY_GB">United Kingdom (GBP)</option>
                        <option value="EBAY_DE">Germany (EUR)</option>
                        <option value="EBAY_AU">Australia (AUD)</option>
                        <option value="EBAY_CA">Canada (CAD)</option>
                    </select>
                    <select id="sortOrder" class="demo-input">
                        <option value="price">Price (Low to High)</option>
                        <option value="-price">Price (High to Low)</option>
                        <option value="newlyListed">Newly Listed</option>
                        <option value="endingSoonest">Ending Soon</option>
                    </select>
                    <button class="btn" onclick="searchProducts()">Search Products</button>
                </div>

                <div id="searchResults" class="demo-results">
                    <p class="loading">Click "Search Products" to see live eBay data...</p>
                </div>
            </div>

            <div id="api" class="tab-content hidden">
                <h3>⚡ Direct eBay API Integration</h3>
                <p>Convert any eBay API Explorer call into working code. Perfect for developers who want full control.</p>

                <div class="endpoint method-post">
                    <strong>POST /api/api-call</strong> - Execute any eBay API endpoint
                </div>

                <div class="demo-controls">
                    <select id="apiMethod" class="demo-input">
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                        <option value="DELETE">DELETE</option>
                    </select>
                    <input type="text" id="apiEndpoint" class="demo-input" placeholder="eBay API endpoint" value="/buy/browse/v1/item_summary/search">
                    <input type="text" id="apiToken" class="demo-input" placeholder="Optional: Your eBay OAuth token">
                    <button class="btn" onclick="testApiCall()">Execute API Call</button>
                </div>

                <div style="margin: 20px 0;">
                    <label><strong>Query Parameters (JSON):</strong></label>
                    <textarea id="apiParams" class="demo-input" rows="3" placeholder='{"q": "drone", "limit": 5}'>{
  "q": "smartphone",
  "limit": 10,
  "sort": "price"
}</textarea>
                </div>

                <div id="apiResults" class="demo-results">
                    <p class="loading">Click "Execute API Call" to test the direct API integration...</p>
                </div>
            </div>

            <div id="features" class="tab-content hidden">
                <h3>🔧 Advanced Features</h3>
                <div class="feature-grid">
                    <div class="feature">
                        <h4>🔐 Multi-Token Authentication</h4>
                        <p>Supports Application Tokens, User OAuth, and manual token override with automatic refresh.</p>
                    </div>
                    <div class="feature">
                        <h4>🌍 Global Marketplaces</h4>
                        <p>Access eBay data from US, UK, Germany, Australia, Canada and 5+ more countries.</p>
                    </div>
                    <div class="feature">
                        <h4>⚡ Rate Limiting</h4>
                        <p>Smart rate limiting with exponential backoff to prevent API throttling.</p>
                    </div>
                    <div class="feature">
                        <h4>🔄 Auto Retry Logic</h4>
                        <p>Automatic retries for failed requests with intelligent error handling.</p>
                    </div>
                    <div class="feature">
                        <h4>📊 Advanced Filters</h4>
                        <p>Price ranges, item conditions, locations, categories, and custom filters.</p>
                    </div>
                    <div class="feature">
                        <h4>🏗️ Production Ready</h4>
                        <p>Comprehensive logging, error handling, and monitoring for enterprise use.</p>
                    </div>
                </div>

                <div class="api-demo">
                    <h4>🧪 Live Feature Test</h4>
                    <div style="display: flex; gap: 15px; flex-wrap: wrap; margin-top: 15px;">
                        <button class="btn" onclick="testConnection()">Test Connection</button>
                        <button class="btn" onclick="testAdvancedSearch()">Advanced Search</button>
                        <button class="btn" onclick="testMarketplaces()">Test Marketplaces</button>
                        <button class="btn" onclick="viewItemDetails()">Item Details</button>
                    </div>
                    <div id="featureResults" class="demo-results">
                        <p class="loading">Click any test button above to see live API responses...</p>
                    </div>
                </div>
            </div>

            <div id="docs" class="tab-content hidden">
                <h3>📚 API Documentation</h3>
                
                <div class="endpoint method-get">
                    <strong>GET /api/search</strong> - Basic product search
                </div>
                <div class="code-block">
curl -X POST "/api/search" \\
  -H "Content-Type: application/json" \\
  -d '{"keyword": "laptop", "limit": 20, "marketplace": "EBAY_US"}'</div>

                <div class="endpoint method-post">
                    <strong>POST /api/search/advanced</strong> - Advanced search with filters
                </div>
                <div class="code-block">
curl -X POST "/api/search/advanced" \\
  -H "Content-Type: application/json" \\
  -d '{
    "keyword": "smartphone",
    "min_price": 100,
    "max_price": 500,
    "condition": "NEW",
    "category_ids": ["9355"]
  }'</div>

                <div class="endpoint method-post">
                    <strong>POST /api/api-call</strong> - Direct eBay API access
                </div>
                <div class="code-block">
curl -X POST "/api/api-call" \\
  -H "Content-Type: application/json" \\
  -d '{
    "method": "GET",
    "endpoint": "/buy/browse/v1/item_summary/search",
    "params": {"q": "drone", "limit": 10},
    "token": "your_ebay_token_here"
  }'</div>

                <div class="endpoint method-get">
                    <strong>GET /api/item/{item_id}</strong> - Get detailed item information
                </div>
                <div class="code-block">
                });
                
                const data = await response.json();
                resultsDiv.innerHTML = `
                    <h4>Advanced Search Results</h4>
                    <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">${JSON.stringify(data, null, 2)}</pre>
                `;
            } catch (error) {
                resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
            }
        }

        async function testMarketplaces() {
            const resultsDiv = document.getElementById('featureResults');
            resultsDiv.innerHTML = '<p class="loading">Loading marketplace info...</p>';
            
            try {
                const response = await fetch('/api/marketplace/info');
                const data = await response.json();
                
                resultsDiv.innerHTML = `
                    <h4>Available Marketplaces</h4>
                    <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">${JSON.stringify(data, null, 2)}</pre>
                `;
            } catch (error) {
                resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
            }
        }

        async function viewItemDetails() {
            const resultsDiv = document.getElementById('featureResults');
            resultsDiv.innerHTML = '<p class="loading">This would show detailed item information...</p>';
            
            // For demo purposes, show the API endpoint documentation
            resultsDiv.innerHTML = `
                <h4>Item Details API</h4>
                <p><strong>Endpoint:</strong> GET /api/item/{item_id}</p>
                <p><strong>Description:</strong> Get detailed information for any eBay item including images, specifications, seller info, and more.</p>
                <div class="code-block">
// Example usage:
const response = await fetch('/api/item/v1|123456789|0?fieldgroups=PRODUCT,EXTENDED');
const itemData = await response.json();
console.log(itemData.item_data);
                </div>
            `;
        }

        // Auto-open search tab on load
        document.addEventListener('DOMContentLoaded', function() {
            openTab('search');
        });
    </script>
</body>
</html>
"""

HTML_ABOUT = """
<!DOCTYPE html>
<html>
<head>
    <title>About - eBay Dropshipping Spy</title>
    <style>
        body{font-family:Arial,Helvetica,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);margin:0;padding:40px;}
        .card{max-width:800px;margin:0 auto;background:#fff;padding:40px;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,0.2);}
        h1{text-align:center;color:#333;margin-bottom:30px;}
        .feature{background:#f8f9fa;padding:20px;margin:20px 0;border-radius:10px;border-left:4px solid #667eea;}
        .btn{display:inline-block;margin:10px 5px;padding:12px 25px;background:#667eea;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;}
        .btn:hover{background:#5a6fd8;}
        .tech-stack{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin:30px 0;}
        .tech{background:#e8f4fd;padding:15px;border-radius:8px;text-align:center;}
    </style>
</head>
<body>
    <div class="card">
        <h1>🚀 About eBay Dropshipping Spy</h1>
        
        <p>A professional-grade eBay product research and API integration platform built for modern dropshipping businesses and developers.</p>
        
        <div class="feature">
            <h3>🎯 What We Do</h3>
            <p>We provide real-time access to eBay's vast product catalog with powerful search, filtering, and analysis tools. Our platform converts complex eBay API calls into simple, developer-friendly endpoints.</p>
        </div>
        
        <div class="feature">
            <h3>⚡ Key Features</h3>
            <ul>
                <li><strong>Universal API Access:</strong> Convert any eBay API Explorer call into working Python code</li>
                <li><strong>Multi-Token Authentication:</strong> Application Tokens, User OAuth, and manual overrides</li>
                <li><strong>Global Marketplace Support:</strong> US, UK, Germany, Australia, Canada, and more</li>
                <li><strong>Advanced Filtering:</strong> Price ranges, conditions, locations, categories</li>
                <li><strong>Production Ready:</strong> Rate limiting, retries, logging, error handling</li>
                <li><strong>Real-time Data:</strong> Live pricing, availability, and seller information</li>
            </ul>
        </div>
        
        <div class="feature">
            <h3>🏗️ Tech Stack</h3>
            <div class="tech-stack">
                <div class="tech">
                    <h4>FastAPI</h4>
                    <p>High-performance async API framework</p>
                </div>
                <div class="tech">
                    <h4>httpx</h4>
                    <p>Modern async HTTP client</p>
                </div>
                <div class="tech">
                    <h4>SQLModel</h4>
                    <p>Type-safe database operations</p>
                </div>
                <div class="tech">
                    <h4>Pydantic</h4>
                    <p>Data validation and serialization</p>
                </div>
            </div>
        </div>
        
        <div class="feature">
            <h3>🔧 For Developers</h3>
            <p>Our platform is designed with developers in mind. Every feature is accessible via clean REST APIs with comprehensive documentation, type safety, and production-grade error handling.</p>
        </div>
        
        <div class="feature">
            <h3>📈 For Businesses</h3>
            <p>Scale your dropshipping operations with reliable access to eBay's product data. Monitor competitor pricing, discover trending products, and automate your research workflows.</p>
        </div>
        
        <div style="text-align:center;margin-top:40px;">
            <a class="btn" href="/">← Back to Home</a>
            <a class="btn" href="/api/docs">API Documentation</a>
            <a class="btn" href="/privacy">Privacy Policy</a>
        </div>
    </div>
</body>
</html>
"""

HTML_PRIVACY = """
<!DOCTYPE html>
<html>
<head>
    <title>Privacy Policy - eBay Dropshipping Spy</title>
    <style>
        body{font-family:Arial,Helvetica,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);margin:0;padding:40px;}
        .card{max-width:700px;margin:0 auto;background:#fff;padding:30px;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,0.2);}
        h1{text-align:center;color:#333;}
        .btn{display:inline-block;margin:10px 0;padding:10px 20px;background:#667eea;color:#fff;text-decoration:none;border-radius:5px;font-weight:600;}
        .btn:hover{background:#5a6fd8;}
        .highlight{background:#e8f4fd;padding:15px;border-radius:8px;margin:15px 0;border-left:4px solid #0066cc;}
    </style>
</head>
<body>
    <div class="card">
        <h1>🔐 Privacy Policy</h1>
        <p>Your privacy is important to us. This policy explains how we collect, use, and protect your information.</p>
        
        <div class="highlight">
            <h3>🛡️ Data Collection</h3>
            <p><strong>Basic Product Search:</strong> No personal data collection. We only use eBay Application Tokens to access public product data.</p>
            <p><strong>Optional eBay Login:</strong> If you choose to connect your eBay account, we store OAuth tokens necessary to access eBay APIs on your behalf.</p>
        </div>
        
        <h3>📊 Data Usage</h3>
        <p>Your data is used solely to provide eBay product search functionality. We never share personal information with third parties.</p>
        
        <h3>🔒 Data Protection</h3>
        <p>All tokens are stored securely using modern encryption. API tokens are automatically refreshed and have limited lifespans.</p>
        
        <h3>🌟 Transparency</h3>
        <p>Our application is open-source and you can review exactly how your data is handled.</p>
        
        <div class="highlight">
            <h3>🚀 Production Features</h3>
            <ul>
                <li>Automatic token refresh and expiration</li>
                <li>Secure environment variable management</li>
                <li>No logging of sensitive information</li>
                <li>Rate limiting to prevent abuse</li>
                <li>Comprehensive error handling</li>
            </ul>
        </div>
        
        <a class="btn" href="/">← Back to Home</a>
    </div>
</body>
</html>
"""

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_HOME

@app.get("/about", response_class=HTMLResponse) 
async def about():
    return HTML_ABOUT

@app.get("/privacy", response_class=HTMLResponse)
async def privacy():
    return HTML_PRIVACY 