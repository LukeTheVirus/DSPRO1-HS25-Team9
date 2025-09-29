from fastapi import APIRouter
from qdrant_client import QdrantClient
import httpx
import os

router = APIRouter()

@router.get("")
async def search_documents(query: str, limit: int = 5):
    # Get embedding for query
    async with httpx.AsyncClient() as client:
        embedding_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embeddings:8001")
        response = await client.post(
            f"{embedding_url}/embed",
            json={"text": query}
        )
        query_embedding = response.json()["embedding"]
    
    # Search Qdrant
    qdrant = QdrantClient(
        host=os.getenv("QDRANT_HOST", "qdrant"),
        port=int(os.getenv("QDRANT_PORT", 6333))
    )
    
    results = qdrant.search(
        collection_name="documents",
        query_vector=query_embedding,
        limit=limit
    )
    
    # Format results
    hits = []
    for result in results:
        hits.append({
            "text": result.payload.get("text"),
            "score": result.score,
            "type": result.payload.get("type"),
            "filename": result.payload.get("filename")
        })
    
    return {"query": query, "results": hits}
