from fastapi import FastAPI
from ..container import Container
from .routers.delete import DeleteRouter
from .routers.generate import GenerateRouter
from .routers.health import HealthRouter
from .routers.ingestion import IngestionRouter
from .routers.search import SearchRouter
from .routers.watcher import WatcherRouter

class Api(FastAPI):
    def __init__(self, container: Container, **kwargs):
        super().__init__(title="RAG MVP Backend", **kwargs)
        self._container = container

        self.get("/")(self.root)

        self.include_routers()

    def include_routers(self):
        self.include_router(DeleteRouter(self._container), prefix="/delete")
        self.include_router(GenerateRouter(self._container), prefix="/generate")
        self.include_router(HealthRouter(self._container))
        self.include_router(IngestionRouter(self._container), prefix="/ingest")
        self.include_router(SearchRouter(self._container), prefix="/search")
        self.include_router(WatcherRouter(self._container), prefix="/watch")

    async def root(self):
        return {
            "message": "RAG MVP Backend",
            "version": "0.1.0",
            "endpoints": ["/health", "/docs", "/ingest", "/search", "/generate"]
        }