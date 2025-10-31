import os
import httpx 


class EmbeddingService:
    def __init__(self):
        self._service_url = os.getenv("EMBEDDING_SERVICE_URL")
        if not self._service_url:
            raise ValueError("EMBEDDING_SERVICE_URL environment variable is not set.")

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        url = f"{self._service_url}/embed/batch"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={"texts": texts})
            response.raise_for_status()
            return response.json().get("embeddings", [])

    async def health_check(self) -> bool:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.get(f"{self._service_url}/health")
                return resp.status_code == 200
            except httpx.RequestError:
                return False

    async def dispose(self):
        pass