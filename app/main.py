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