from fastapi import FastAPI
from .routers import health

app = FastAPI(title="RAG MVP Backend")

app.include_router(health.router, tags=["health"])

@app.get("/")
async def root():
    return {
        "message": "RAG MVP Backend",
        "version": "0.1.0",
        "endpoints": ["/health", "/docs"]
    }
