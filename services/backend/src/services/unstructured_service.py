import os

from httpx import AsyncClient


class UnstructuredService:
    def __init__(self):
        self._http_client = AsyncClient(timeout=30.0)
        self._service_url = os.getenv("UNSTRUCTURED_SERVICE_URL")
        if not self._service_url:
            raise ValueError("UNSTRUCTURED_SERVICE_URL environment variable is not set.")

    async def parse_document(self, file_name: str, content_type: str, content: bytes) -> dict:
        url = f"{self._service_url}/parse"
        files = {"file": (file_name, content, content_type)}
        response = await self._http_client.post(url, files=files)
        return response.json()

    async def health_check(self) -> bool:
        resp = await self._http_client.get(f"{self._service_url}/health", timeout=5.0)
        return resp.status_code == 200

    async def dispose(self):
        await self._http_client.aclose()
