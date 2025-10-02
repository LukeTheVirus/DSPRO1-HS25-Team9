from fastapi import FastAPI
from .routers import health, ingestion, search, delete, watcher



app = FastAPI(title="RAG MVP Backend")

app.include_router(health.router, tags=["health"])
app.include_router(ingestion.router, prefix="/ingest", tags=["ingestion"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(delete.router, prefix="/delete", tags=["delete"])
app.include_router(watcher.router, prefix="/watch", tags=["watcher"])

@app.get("/")
async def root():
    return {
        "message": "RAG MVP Backend",
        "version": "0.1.0",
        "endpoints": ["/health", "/docs", "/ingest", "/search"]
    }
