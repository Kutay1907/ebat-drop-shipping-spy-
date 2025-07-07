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
        .btn{display:inline-block;margin:10px 0;padding:10px 20px;background:#0064d2;color:#fff;text-decoration:none;border-radius:5px;}
        input[type=text]{width:70%;padding:10px;border:1px solid #ccc;border-radius:5px;}
    </style>
</head>
<body>
    <div class="card">
        <h1>🛍️ Revolist</h1>
        <p>Connect your eBay account and start searching profitable items.</p>
        <div>
            <a class="btn" href="/auth/login">🔑 Connect with eBay</a>
            <a class="btn" href="/about">ℹ️ About</a>
            <a class="btn" href="/privacy">🛡️ Privacy</a>
            <a class="btn" href="/health">💓 Health</a>
            <a class="btn" href="/docs">📄 API Docs</a>
        </div>
        <hr>
        <h3>Quick Search</h3>
        <form id="searchForm">
            <input type="text" id="keyword" placeholder="Enter keyword…" required>
            <button class="btn" type="submit">Search</button>
        </form>
        <pre id="results"></pre>
    </div>
<script>
document.getElementById('searchForm').addEventListener('submit',async(e)=>{
  e.preventDefault();
  const kw=document.getElementById('keyword').value.trim();
  if(!kw) return;
  try {
    const res=await fetch('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({keyword:kw})});
    const data=await res.json();
    document.getElementById('results').textContent=JSON.stringify(data,null,2);
  } catch(err) {
    document.getElementById('results').textContent='Error: ' + err.message;
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
        <p>Features:</p>
        <ul>
            <li>Real-time eBay product search</li>
            <li>OAuth integration with eBay</li>
            <li>Product analytics and insights</li>
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
        <p>We only collect OAuth tokens necessary to access eBay APIs on your behalf.</p>
        <h3>Data Usage</h3>
        <p>Your data is used solely to provide eBay product search functionality.</p>
        <h3>Data Protection</h3>
        <p>All data is stored securely and is not shared with third parties.</p>
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