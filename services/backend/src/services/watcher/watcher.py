import asyncio
import mimetypes
import threading
from pathlib import Path

from ..document.document_service import DocumentService

SUPPORTED_EXTENSIONS = {
    '.pdf', '.txt', '.docx', '.doc', '.pptx', '.ppt',
    '.html', '.xml', '.json', '.csv', '.md', '.mdx', '.rtf',
    '.epub', '.msg', '.eml'
}


class Watcher:
    def __init__(self, document_service: DocumentService):
        self.watching_directory = None
        self.processed_files = {}
        self.currently_processing = 0
        self.files_being_ingested = 0

        self._document_service = document_service
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
        print("Watcher started")
        while not self._is_stopped:
            try:
                asyncio.run(self._watch_directory())
            except Exception as e:
                print(f"Watcher thread error: {e}")

    async def _watch_directory(self):
        directory_path = self.watching_directory

        while not self._is_stopped:
            try:
                directory = Path(directory_path)
                if directory.exists():
                    # Find all current files with their modification times
                    current_files = {}
                    for ext in SUPPORTED_EXTENSIONS:
                        for file in directory.rglob(f"*{ext}"):
                            if file.is_file():
                                path = str(file.resolve())
                                current_files[path] = file.stat().st_mtime

                    # Count files that need processing
                    files_to_process = []
                    for path, mtime in current_files.items():
                        if path not in self.processed_files:
                            files_to_process.append(('new', path, mtime))
                        elif self.processed_files[path] < mtime:
                            files_to_process.append(('modified', path, mtime))

                    # Also count deleted files
                    deleted_files = set(self.processed_files.keys()) - set(current_files.keys())
                    for path in deleted_files:
                        files_to_process.append(('deleted', path, None))

                    # Set count
                    self.currently_processing = len(files_to_process)

                    # Process files
                    for action, path, mtime in files_to_process:
                        self.files_being_ingested += 1
                        self.currently_processing -= 1
                        file = Path(path)

                        if action == 'new':
                            print(f"Found new file: {path}")
                            await self._ingest_file_async(file)
                            self.processed_files[path] = mtime
                        elif action == 'modified':
                            print(f"File modified: {path}")
                            await self._delete_file_async(file)
                            await self._ingest_file_async(file)
                            self.processed_files[path] = mtime
                        elif action == 'deleted':
                            print(f"File deleted: {path}")
                            await self._delete_file_async(file)
                            del self.processed_files[path]

                        self.files_being_ingested -= 1

            except Exception as e:
                print(f"Watch error: {e}")

            await asyncio.sleep(10)

    async def _ingest_file_async(self, file: Path):
        identifier = Watcher._build_identifier(file)
        file_content = file.read_bytes()
        content_type = mimetypes.guess_type(str(file.resolve()))[0] or "application/octet-stream"
        await self._document_service.insert_document(identifier, file_content, content_type)

    async def _delete_file_async(self, file_path: Path):
        identifier = Watcher._build_identifier(file_path)
        await self._document_service.delete_by_identifier(identifier)

    @staticmethod
    def _build_identifier(file: Path) -> str:
        return str(file.resolve())
