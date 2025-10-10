import asyncio
import threading
from pathlib import Path
from typing import Dict

import httpx

SUPPORTED_EXTENSIONS = {
    '.pdf', '.txt', '.docx', '.doc', '.pptx', '.ppt',
    '.html', '.xml', '.json', '.csv', '.md', '.rtf',
    '.epub', '.msg', '.eml'
}


class WatcherService:
    def __init__(self):
        self.watchers: Dict[str, "Watcher"] = {}

    def start_watching(self, directory: str):
        directory = str(Path(directory).resolve())

        if directory in self.watchers:
            return {"status": "already_watching"}

        Path(directory).mkdir(parents=True, exist_ok=True)

        watcher = Watcher()
        self.watchers[directory] = watcher

        watcher.start_watching(directory)

        return {"status": "started"}

    def stop_watching(self, directory: str):
        directory = str(Path(directory).resolve())
        if directory not in self.watchers:
            return {"status": "not_watching"}

        self.watchers[directory].stop_watching()
        del self.watchers[directory]

        return {"status": "stopped"}

    def get_status(self):
        watchers = []
        for watcher in self.watchers.values():
            watchers.append({
                "directory": watcher.watching_directory,
                "tracked_files": len(watcher.processed_files),
                "currently_processing": watcher.currently_processing,
                "files_being_ingested": watcher.files_being_ingested
            })

        return {"watchers": watchers}


class Watcher:
    def __init__(self):
        self.watching_directory = None
        self.processed_files = {}
        self.currently_processing = 0
        self.files_being_ingested = 0

        self._is_running = False
        self._is_stopped = False
        self._watcher_thread = None

    def start_watching(self, directory: str):
        if self._is_running:
            raise Exception("Already watching a directory")
        self._is_running = True
        self.watching_directory = directory

        self._watcher_thread = threading.Thread(target=self._start_thread)
        self._watcher_thread.daemon = True
        self._watcher_thread.start()

    def stop_watching(self):
        if not self._is_running or self._is_stopped:
            return
        self._is_stopped = True
        if self._watcher_thread:
            self._watcher_thread.join()

    def _start_thread(self):
        asyncio.run(self._watch_directory())

    async def _watch_directory(self):
        directory = self.watching_directory

        while not self._is_stopped:
            try:
                path = Path(directory)
                if path.exists():
                    # Find all current files with their modification times
                    current_files = {}
                    for ext in SUPPORTED_EXTENSIONS:
                        for file_path in path.rglob(f"*{ext}"):
                            current_files[str(file_path)] = file_path.stat().st_mtime

                    # Count files that need processing
                    files_to_process = []
                    for file_path_str, mtime in current_files.items():
                        if file_path_str not in self.processed_files:
                            files_to_process.append(('new', file_path_str, mtime))
                        elif self.processed_files[file_path_str] < mtime:
                            files_to_process.append(('modified', file_path_str, mtime))

                    # Also count deleted files
                    deleted_files = set(self.processed_files.keys()) - set(current_files.keys())
                    for file_path_str in deleted_files:
                        files_to_process.append(('deleted', file_path_str, None))

                    # Set count
                    self.currently_processing = len(files_to_process)

                    # Process files
                    for action, file_path_str, mtime in files_to_process:
                        self.files_being_ingested += 1
                        self.currently_processing -= 1

                        if action == 'new':
                            print(f"Found new file: {file_path_str}")
                            await self._ingest_file_async(Path(file_path_str))
                            self.processed_files[file_path_str] = mtime
                        elif action == 'modified':
                            print(f"File modified: {file_path_str}")
                            await self._delete_file_async(Path(file_path_str))
                            await self._ingest_file_async(Path(file_path_str))
                            self.processed_files[file_path_str] = mtime
                        elif action == 'deleted':
                            print(f"File deleted: {file_path_str}")
                            await self._delete_file_async(Path(file_path_str))
                            del self.processed_files[file_path_str]

                        self.files_being_ingested -= 1

            except Exception as e:
                print(f"Watch error: {e}")

            await asyncio.sleep(10)

    async def _ingest_file_async(self, file_path: Path):
        """Call ingestion endpoint for a file"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(file_path, 'rb') as f:
                    files = {'file': (file_path.name, f, 'application/octet-stream')}
                    response = await client.post(
                        "http://localhost:8000/ingest/file",
                        files=files,
                        data={'source_path': str(file_path)}
                    )
            return response.json()
        except Exception as e:
            print(f"Error ingesting {file_path}: {e}")
            return None

    async def _delete_file_async(self, file_path: Path):
        """Call deletion endpoint for a file"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    "http://localhost:8000/delete/by-path",
                    params={'source_path': str(file_path)}
                )
            return response.json()
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
            return None
