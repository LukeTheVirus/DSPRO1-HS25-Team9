from dependency_injector import containers, providers

from .services.embedding_service import EmbeddingService
from .services.ollama_service import OllamaService
from .services.qdrant_service import QdrantService
from .services.unstructured_service import UnstructuredService
from . import workflow_controller

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=[
        ".routers.health",
        ".routers.search",
        ".routers.ingestion",
        ".routers.delete",
        ".routers.watcher"
    ])

    embedding_service = providers.Singleton(EmbeddingService)
    ollama_service = providers.Singleton(OllamaService)
    qdrant_service = providers.Singleton(QdrantService)
    unstructured_service = providers.Singleton(UnstructuredService)
    workflow_controller = providers.Factory(workflow_controller.call_workflow)
