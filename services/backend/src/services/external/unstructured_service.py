import os
import httpx


class UnstructuredService:
    def __init__(self):
        self._service_url = os.getenv("UNSTRUCTURED_SERVICE_URL")
        if not self._service_url:
            raise ValueError("UNSTRUCTURED_SERVICE_URL environment variable is not set.")

    async def parse_document(self, filename: str, content_type: str, content: bytes) -> dict:
        url = f"{self._service_url}/parse"
        files = {"file": (filename, content, content_type)}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, files=files)
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.get(f"{self._service_url}/health")
                return resp.status_code == 200
            except httpx.RequestError:
                return False

    async def dispose(self):
        pass