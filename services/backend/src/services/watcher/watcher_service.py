from pathlib import Path
from typing import Dict

from .watcher import Watcher
from ..document.document_service import DocumentService


class WatcherService:
    def __init__(self, document_service: DocumentService):
        self._watchers: Dict[str, Watcher] = {}
        self._document_service = document_service

    def start_watching(self, directory: str):
        directory = str(Path(directory).resolve())

        if directory in self._watchers:
            return {"status": "already_watching"}

        Path(directory).mkdir(parents=True, exist_ok=True)

        watcher = Watcher(self._document_service)
        self._watchers[directory] = watcher

        watcher.start_watching(directory)

        return {"status": "started"}

    def stop_watching(self, directory: str):
        directory = str(Path(directory).resolve())
        if directory not in self._watchers:
            return {"status": "not_watching"}

        self._watchers[directory].stop_watching()
        del self._watchers[directory]

        return {"status": "stopped"}

    def get_status(self):
        watchers = []
        for watcher in self._watchers.values():
            watchers.append({
                "directory": watcher.watching_directory,
                "tracked_files": len(watcher.processed_files),
                "currently_processing": watcher.currently_processing,
                "files_being_ingested": watcher.files_being_ingested
            })

        return {"watchers": watchers}
