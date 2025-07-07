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


app = FastAPI(title="Revolist API", version="1.0.0", lifespan=lifespan)

# Import and register routes after app creation
try:
    from app.auth_routes import router as auth_router
    from app.search_routes import router as search_router
    
    app.include_router(auth_router)
    app.include_router(search_router)
    logger.info("Routes registered successfully")
except Exception as e:
    logger.error(f"Failed to register routes: {e}")

# Health
@app.get("/health")
async def health():
    return {"status": "ok", "service": "revolist-api"}

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

HTML_HOME = """
<!DOCTYPE html>
<html>
<head>
    <title>Revolist – eBay Dropshipping Tool</title>
    <style>
        body{font-family:Arial,Helvetica,sans-serif;background:#f5f5f5;margin:0;padding:40px;}
        .card{max-width:700px;margin:0 auto;background:#fff;padding:30px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
        h1{text-align:center;color:#333;}
        .btn{display:inline-block;margin:10px 0;padding:10px 20px;background:#0064d2;color:#fff;text-decoration:none;border-radius:5px;text-decoration:none;}
        .btn:hover{background:#0056b3;}
        .btn.secondary{background:#6c757d;}
        .btn.test{background:#28a745;}
        input[type=text]{width:70%;padding:10px;border:1px solid #ccc;border-radius:5px;}
        .status{margin:10px 0;padding:10px;border-radius:5px;}
        .success{background:#d4edda;color:#155724;border:1px solid #c3e6cb;}
        .error{background:#f8d7da;color:#721c24;border:1px solid #f5c6cb;}
        .info{background:#d1ecf1;color:#0c5460;border:1px solid #bee5eb;}
    </style>
</head>
<body>
    <div class="card">
        <h1>🛍️ Revolist</h1>
        <p><strong>eBay Dropshipping Research Tool</strong></p>
        
        <div class="info">
            <strong>✅ No eBay Login Required!</strong><br>
            Product search works immediately with just your API credentials.
        </div>
        
        <div>
            <a class="btn test" href="#" onclick="testToken()">🧪 Test eBay Connection</a>
            <a class="btn secondary" href="/auth/login">🔑 Advanced: Connect eBay Account</a>
            <a class="btn secondary" href="/about">ℹ️ About</a>
            <a class="btn secondary" href="/privacy">🛡️ Privacy</a>
            <a class="btn secondary" href="/health">💓 Health</a>
            <a class="btn secondary" href="/docs">📄 API Docs</a>
        </div>
        
        <div id="tokenStatus"></div>
        
        <hr>
        <h3>🔍 Product Search</h3>
        <form id="searchForm">
            <input type="text" id="keyword" placeholder="Enter keyword (e.g., 'laptop', 'drone', 'shoes')..." required>
            <button class="btn" type="submit">Search eBay</button>
        </form>
        
        <div id="searchStatus"></div>
        <pre id="results"></pre>
    </div>

<script>
async function testToken() {
    const statusDiv = document.getElementById('tokenStatus');
    statusDiv.innerHTML = '<div class="info">Testing eBay API connection...</div>';
    
    try {
        const res = await fetch('/api/search/test-token');
        const data = await res.json();
        
        if (data.status === 'success') {
            statusDiv.innerHTML = `<div class="success">✅ ${data.message}<br>Token: ${data.token_preview} (${data.token_length} chars)</div>`;
        } else {
            statusDiv.innerHTML = `<div class="error">❌ ${data.message}<br>Check: ${data.check?.join(', ')}</div>`;
        }
    } catch (err) {
        statusDiv.innerHTML = `<div class="error">❌ Connection test failed: ${err.message}</div>`;
    }
}

document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const kw = document.getElementById('keyword').value.trim();
    const statusDiv = document.getElementById('searchStatus');
    const resultsDiv = document.getElementById('results');
    
    if (!kw) return;
    
    statusDiv.innerHTML = '<div class="info">Searching eBay products...</div>';
    resultsDiv.textContent = '';
    
    try {
        const res = await fetch('/api/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({keyword: kw})
        });
        
        const data = await res.json();
        
        if (res.ok) {
            statusDiv.innerHTML = `<div class="success">✅ Found ${data.total_found} products for "${data.keyword}"</div>`;
            resultsDiv.textContent = JSON.stringify(data, null, 2);
        } else {
            statusDiv.innerHTML = `<div class="error">❌ Search failed: ${data.detail}</div>`;
        }
    } catch (err) {
        statusDiv.innerHTML = `<div class="error">❌ Search error: ${err.message}</div>`;
    }
});
</script>
</body>
</html>
"""

HTML_ABOUT = """
<!DOCTYPE html>
<html>
<head>
    <title>About - Revolist</title>
    <style>
        body{font-family:Arial,Helvetica,sans-serif;background:#f5f5f5;margin:0;padding:40px;}
        .card{max-width:700px;margin:0 auto;background:#fff;padding:30px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
        h1{text-align:center;color:#333;}
        .btn{display:inline-block;margin:10px 0;padding:10px 20px;background:#0064d2;color:#fff;text-decoration:none;border-radius:5px;}
    </style>
</head>
<body>
    <div class="card">
        <h1>About Revolist</h1>
        <p>Revolist is a powerful eBay dropshipping research tool that helps you find profitable products to sell.</p>
        
        <h3>🚀 Features</h3>
        <ul>
            <li><strong>Instant Product Search</strong> - No eBay login required for basic searches</li>
            <li><strong>Real-time eBay Data</strong> - Direct access to eBay Browse API</li>
            <li><strong>Application Token Auth</strong> - Seamless API access</li>
            <li><strong>Optional OAuth Integration</strong> - For advanced user-specific features</li>
            <li><strong>Product Analytics</strong> - Detailed item information and insights</li>
        </ul>
        
        <h3>🔧 How It Works</h3>
        <p>Revolist uses eBay's official Application Token system (Client Credentials flow) for public product data. This means:</p>
        <ul>
            <li>✅ Immediate access - no user consent required</li>
            <li>✅ Automatic token refresh</li>
            <li>✅ Full eBay Browse API access</li>
            <li>✅ Real-time product data</li>
        </ul>
        
        <a class="btn" href="/">← Back to Home</a>
    </div>
</body>
</html>
"""

HTML_PRIVACY = """
<!DOCTYPE html>
<html>
<head>
    <title>Privacy Policy - Revolist</title>
    <style>
        body{font-family:Arial,Helvetica,sans-serif;background:#f5f5f5;margin:0;padding:40px;}
        .card{max-width:700px;margin:0 auto;background:#fff;padding:30px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);}
        h1{text-align:center;color:#333;}
        .btn{display:inline-block;margin:10px 0;padding:10px 20px;background:#0064d2;color:#fff;text-decoration:none;border-radius:5px;}
    </style>
</head>
<body>
    <div class="card">
        <h1>Privacy Policy</h1>
        <p>Your privacy is important to us. This policy explains how we collect, use, and protect your information.</p>
        <h3>Data Collection</h3>
        <p><strong>Basic Product Search:</strong> No personal data collection. We only use eBay Application Tokens to access public product data.</p>
        <p><strong>Optional eBay Login:</strong> If you choose to connect your eBay account, we store OAuth tokens necessary to access eBay APIs on your behalf.</p>
        <h3>Data Usage</h3>
        <p>Your data is used solely to provide eBay product search functionality. We never share personal information with third parties.</p>
        <h3>Data Protection</h3>
        <p>All tokens are stored securely using modern encryption. API tokens are automatically refreshed and have limited lifespans.</p>
        <h3>Transparency</h3>
        <p>Our application is open-source and you can review exactly how your data is handled.</p>
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