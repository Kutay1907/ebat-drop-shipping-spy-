from fastapi import FastAPI
from .auth_routes import router as auth_router
from .search_routes import router as search_router

app = FastAPI(title="Revolist API", version="1.0.0")

app.include_router(auth_router)
app.include_router(search_router)

# Health
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    from .database import init_db
    await init_db()

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
  const res=await fetch('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({keyword:kw})});
  const data=await res.json();
  document.getElementById('results').textContent=JSON.stringify(data,null,2);
});
</script>
</body>
</html>
"""

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_HOME 