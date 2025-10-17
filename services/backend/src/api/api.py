from fastapi import FastAPI

from .routers.generate import GenerateRouter
from .routers.health import HealthRouter
from .routers.watcher import WatcherRouter
from ..container import Container


class Api(FastAPI):
    def __init__(self, container: Container, **kwargs):
        super().__init__(title="RAG MVP Backend", **kwargs)
        self._container = container

        self.get("/")(Api.root)

        self.include_routers()

    def include_routers(self):
        self.include_router(GenerateRouter(self._container), prefix="/generate")
        self.include_router(HealthRouter(self._container))
        self.include_router(WatcherRouter(self._container), prefix="/watch")

    @staticmethod
    async def root():
        return {
            "message": "RAG MVP Backend",
            "version": "0.1.0",
            "endpoints": ["/health", "/docs", "/ingest", "/search", "/generate"]
        }
