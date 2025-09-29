from fastapi import APIRouter
from qdrant_client import QdrantClient
import httpx
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    status = {"status": "healthy", "services": {}}
    
    # Check QDrant
    try:
        qdrant = QdrantClient(
            host=os.getenv("QDRANT_HOST", "qdrant"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
        collections = qdrant.get_collections()
        status["services"]["qdrant"] = {
            "status": "connected",
            "collections": len(collections.collections)
        }
    except Exception as e:
        status["services"]["qdrant"] = {"status": "error", "error": str(e)}
        status["status"] = "degraded"
    
    # Check Ollama
    try:
        async with httpx.AsyncClient() as client:
            ollama_host = os.getenv("OLLAMA_HOST", "ollama")
            ollama_port = int(os.getenv("OLLAMA_PORT", 11434))
            resp = await client.get(f"http://{ollama_host}:{ollama_port}/api/tags", timeout=5.0)
            status["services"]["ollama"] = {"status": "connected"}
    except Exception as e:
        status["services"]["ollama"] = {"status": "error", "error": str(e)}
        status["status"] = "degraded"
    
    # Check Embedding Service
    try:
        async with httpx.AsyncClient() as client:
            embedding_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embeddings:8001")
            resp = await client.get(f"{embedding_url}/health", timeout=5.0)
            status["services"]["embeddings"] = {"status": "connected"}
    except Exception as e:
        status["services"]["embeddings"] = {"status": "error", "error": str(e)}
        status["status"] = "degraded"
    
    # Check Unstructured Service
    try:
        async with httpx.AsyncClient() as client:
            unstructured_url = os.getenv("UNSTRUCTURED_SERVICE_URL", "http://unstructured:8002")
            resp = await client.get(f"{unstructured_url}/health", timeout=5.0)
            status["services"]["unstructured"] = {"status": "connected"}
    except Exception as e:
        status["services"]["unstructured"] = {"status": "error", "error": str(e)}
        status["status"] = "degraded"
    
    return status
