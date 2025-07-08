import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.search_routes import router as search_router

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"

app = FastAPI(
    title="Ebay Product Search",
    description="A simple API to search for products on eBay.",
    version="1.0.0"
)

STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(search_router)

@app.get("/", response_class=FileResponse)
async def read_root():
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        return HTMLResponse(content="<h1>Error: index.html not found</h1><p>Please make sure the static/index.html file exists.</p>", status_code=404)
    return FileResponse(index_path)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )