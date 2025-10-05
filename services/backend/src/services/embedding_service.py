import os
from httpx import AsyncClient

class EmbeddingService:
    def __init__(self):
        self._http_client = AsyncClient(timeout=30.0)
        self._service_url = os.getenv("EMBEDDING_SERVICE_URL")
        if not self._service_url:
            raise ValueError("EMBEDDING_SERVICE_URL environment variable is not set.")
        
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        url = f"{self._service_url}/embed/batch"
        response = await self._http_client.post(url, json={"texts": texts})
        response.raise_for_status()
        return response.json().get("embeddings", [])

    async def dispose(self):
        await self._http_client.aclose()