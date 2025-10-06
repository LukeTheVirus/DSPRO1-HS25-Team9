from typing import Annotated
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from ..container import Container
from ..services.embedding_service import EmbeddingService
from ..services.ollama_service import OllamaService
from ..services.qdrant_service import QdrantService
from ..services.unstructured_service import UnstructuredService
import httpx
import os

router = APIRouter()

@router.get("/health")
@inject
async def health_check(
    embedding_service: Annotated[EmbeddingService, Depends(Provide[Container.embedding_service])],
    ollama_service: Annotated[OllamaService, Depends(Provide[Container.ollama_service])],
    qdrant_service: Annotated[QdrantService, Depends(Provide[Container.qdrant_service])],
    unstructured_service: Annotated[UnstructuredService, Depends(Provide[Container.unstructured_service])],
):
    status = {"status": "healthy", "services": {}}
    
    status = await check_service("qdrant", status, qdrant_service.health_check)
    status = await check_service("embeddings", status, embedding_service.health_check)
    status = await check_service("unstructured", status, unstructured_service.health_check)
    status = await check_service("ollama", status, ollama_service.health_check)

    return status

async def check_service(name: str, status: dict, check_func: callable):
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
    return status
