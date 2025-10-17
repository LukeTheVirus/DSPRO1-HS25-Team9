from .document.document_service import DocumentService
from .external.embedding_service import EmbeddingService
from .external.ollama_service import OllamaService
from .external.qdrant_service import QdrantService
from .external.unstructured_service import UnstructuredService
from .watcher.watcher_service import WatcherService
from ..container import Module, Container


class ServiceModule(Module):
    def register_services(self, container: Container):
        container.register_singleton(EmbeddingService)
        container.register_singleton(OllamaService)
        container.register_singleton(UnstructuredService)
        container.register_singleton(QdrantService)
        container.register_singleton(DocumentService)
        container.register_singleton(WatcherService)
