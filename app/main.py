import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.search_routes import router as search_router
from app.debug_routes import router as debug_router
from app.favorites_routes import router as favorites_router
from app.auth_routes import router as auth_router
from app.listing_routes import router as listing_router
from .database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"

app = FastAPI(
    title="eBay Dropshipping Spy & Seller Tool",
    description="A powerful tool for eBay product research, analysis, and seller management.",
    version="2.0.0"
)

STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(search_router)
app.include_router(debug_router)
app.include_router(favorites_router)
app.include_router(auth_router)
app.include_router(listing_router)

@app.get("/", response_class=FileResponse)
async def read_root():
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        return HTMLResponse(content="<h1>Error: index.html not found</h1><p>Please make sure the static/index.html file exists.</p>", status_code=404)
    return FileResponse(index_path)

@app.get("/auth/success")
async def auth_success():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ebay-dropshipping-spy"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )