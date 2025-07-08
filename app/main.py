import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Import the simplified search router
from app.search_routes import router as search_router

# Define the project root and static directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"

# Create the main FastAPI application
app = FastAPI(
    title="Ebay Product Search",
    description="A simple API to search for products on eBay.",
    version="1.0.0"
)

# Ensure the static directory exists
STATIC_DIR.mkdir(exist_ok=True)

# Mount the static directory to serve files like CSS and JS
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include the API router for handling search requests
app.include_router(search_router)

@app.get("/", response_class=FileResponse)
async def read_root():
    """
    Serves the main index.html file from the static directory.
    """
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        # Return a simple HTML response if index.html is not found
        return HTMLResponse(content="<h1>Error: index.html not found</h1><p>Please make sure the static/index.html file exists.</p>", status_code=404)
    return FileResponse(index_path)

# Main execution block to run the app with uvicorn for local development
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

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