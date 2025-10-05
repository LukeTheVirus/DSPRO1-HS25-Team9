from dependency_injector import containers, providers
from .services.qdrant_service import QdrantService
from .services.unstructured_service import UnstructuredService
from .services.embedding_service import EmbeddingService

class Container(containers.DeclarativeContainer):
    qdrant_service = providers.Singleton(QdrantService)
    unstructured_service = providers.Singleton(UnstructuredService)
    embedding_service = providers.Singleton(EmbeddingService)
