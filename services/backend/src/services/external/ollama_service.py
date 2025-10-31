import os
import httpx


class OllamaService:
    def __init__(self):
        self._service_url = os.getenv("OLLAMA_SERVICE_URL")
        if not self._service_url:
            raise ValueError("OLLAMA_SERVICE_URL environment variable is not set.")

    async def generate_response(self, model: str, prompt: str, stream: bool = False) -> str:
        url = f"{self._service_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status() 
                response_json = response.json()
                return response_json.get("response", "")
            except Exception as e:
                print(f"Error calling Ollama: {e}")
                raise

    async def health_check(self) -> bool:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.get(f"{self._service_url}/api/tags")
                return resp.status_code == 200
            except httpx.RequestError:
                return False

    async def dispose(self):
        pass