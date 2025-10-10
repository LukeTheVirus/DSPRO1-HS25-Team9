from typing import Awaitable, Callable
from fastapi import APIRouter
from ...container import Container
from ...services.qdrant_service import QdrantService
from ...services.embedding_service import EmbeddingService
from ...services.ollama_service import OllamaService
from ...services.unstructured_service import UnstructuredService


class HealthRouter(APIRouter):
    def __init__(self, container: Container, **kwargs):
        super().__init__(**kwargs)
        self._container = container

        self.get("/health")(self.health_check)

    async def health_check(self):
        qdrant_service = self._container.resolve(QdrantService)
        embedding_service = self._container.resolve(EmbeddingService)
        unstructured_service = self._container.resolve(UnstructuredService)
        ollama_service = self._container.resolve(OllamaService)
        
        status = {"status": "healthy", "services": {}}
        
        await HealthRouter._check_service("qdrant", status, qdrant_service.health_check)
        await HealthRouter._check_service("embeddings", status, embedding_service.health_check)
        await HealthRouter._check_service("unstructured", status, unstructured_service.health_check)
        await HealthRouter._check_service("ollama", status, ollama_service.health_check)

        return status

    @staticmethod    
    async def _check_service(name: str, status: dict, check_func: Callable[[], Awaitable[bool]]):
        try:
            if await check_func():
                result = {"status": "healthy"}
            else:
                raise Exception("Service returned unhealthy status")
        except Exception as e:
            result = {"status": "error", "error": str(e)}
            
        status["services"][name] = result
        if result["status"] == "error":
            status["status"] = "degraded"
