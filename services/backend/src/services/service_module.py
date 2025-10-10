from ..container import Module, Container
from .embedding_service import EmbeddingService
from .ollama_service import OllamaService
from .unstructured_service import UnstructuredService
from .qdrant_service import QdrantService
from .watcher_service import WatcherService

class ServiceModule(Module):
    def register_services(self, container: Container):
        container.register_singleton(EmbeddingService)
        container.register_singleton(OllamaService)
        container.register_singleton(UnstructuredService)
        container.register_singleton(QdrantService)
        container.register_singleton(WatcherService)