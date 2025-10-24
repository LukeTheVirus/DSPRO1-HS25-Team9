import os

from httpx import AsyncClient


class OllamaService:
    def __init__(self):
        self._http_client = AsyncClient(timeout=30.0)
        self._service_url = os.getenv("OLLAMA_SERVICE_URL")
        if not self._service_url:
            raise ValueError("OLLAMA_SERVICE_URL environment variable is not set.")

    async def generate_response(self, model: str, prompt: str, stream: bool = False) -> str:
        """
        Sends a prompt to the Ollama service to generate a response.
        """
        url = f"{self._service_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream  # We'll default to non-streaming for simplicity
        }
        
        try:
            response = await self._http_client.post(url, json=payload, timeout=120.0) # Give generation more time
            response.raise_for_status() # Raise an exception for 4xx or 5xx status codes
            
            response_json = response.json()
            
            # For non-streaming, the response is a single JSON object
            # The actual text is in the 'response' key
            return response_json.get("response", "")
            
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            # Re-raise or return a specific error message
            raise

    async def health_check(self) -> bool:
        try:
            resp = await self._http_client.get(f"{self._service_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def dispose(self):
        await self._http_client.aclose()