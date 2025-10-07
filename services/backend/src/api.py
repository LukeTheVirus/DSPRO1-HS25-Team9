from fastapi import FastAPI
from .routers import health, ingestion, search, delete, watcher, generate
from .container import Container

class Api:
    def __init__(self, container: Container):
        self._app = FastAPI(title="RAG MVP Backend")
        self._app.container = container

        self._app.get("/")(self.root)

        self.include_routers(self._app)

    def include_routers(self, app: FastAPI):
        app.include_router(health.router)
        app.include_router(ingestion.router, prefix="/ingest")
        app.include_router(search.router, prefix="/search")
        app.include_router(delete.router, prefix="/delete")
        app.include_router(watcher.router, prefix="/watch")
        app.include_router(generate.router, prefix="/generate")


    def get_app(self):
        return self._app

    async def root(self):
        return {
            "message": "RAG MVP Backend",
            "version": "0.1.0",
            "endpoints": ["/health", "/docs", "/ingest", "/search", "/generate"]
        }