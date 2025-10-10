from fastapi import APIRouter
from ...container import Container
from ...services.watcher_service import WatcherService

class WatcherRouter(APIRouter):
    def __init__(self, container: Container, **kwargs):
        super().__init__(**kwargs)
        self._container = container

        self.post("/start")(self.start_watching)
        self.post("/stop")(self.stop_watching_endpoint)
        self.get("/status")(self.get_status)
        
    def start_watching(self, directory: str):
        watcher_service = self._container.resolve(WatcherService)
        return watcher_service.start_watching(directory)

    def stop_watching_endpoint(self):
        watcher_service = self._container.resolve(WatcherService)
        return watcher_service.stop_watching()

    def get_status(self):
        watcher_service = self._container.resolve(WatcherService)
        return watcher_service.get_status()