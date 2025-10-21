import os

from httpx import AsyncClient


class OllamaService:
    def __init__(self):
        self._http_client = AsyncClient(timeout=30.0)
        self._service_url = os.getenv("OLLAMA_SERVICE_URL")
        if not self._service_url:
            raise ValueError("OLLAMA_SERVICE_URL environment variable is not set.")

    async def health_check(self) -> bool:
        resp = await self._http_client.get(f"{self._service_url}/api/tags", timeout=5.0)
        return resp.status_code == 200

    async def dispose(self):
        await self._http_client.aclose()
