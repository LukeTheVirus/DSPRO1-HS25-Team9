from fastapi import APIRouter
from pathlib import Path
import asyncio
import httpx
import threading
import time

router = APIRouter()
# Global state
watcher_thread = None
stop_watching = False
processed_files = {}  # Track files with modification time: {path: mtime}
watching_directory = None
currently_processing = 0
files_being_ingested = 0

SUPPORTED_EXTENSIONS = {
    '.pdf', '.txt', '.docx', '.doc', '.pptx', '.ppt',
    '.html', '.xml', '.json', '.csv', '.md', '.rtf',
    '.epub', '.msg', '.eml'
}

async def ingest_file_async(file_path: Path):
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

async def delete_file_async(file_path: Path):
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

def watch_directory(directory: str):
    """Simple blocking watcher in a thread"""
    global stop_watching, processed_files, watching_directory, currently_processing, files_being_ingested
    
    processed_files = {}  # Reset on start
    watching_directory = directory
    
    while not stop_watching:
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
                    if file_path_str not in processed_files:
                        files_to_process.append(('new', file_path_str, mtime))
                    elif processed_files[file_path_str] < mtime:
                        files_to_process.append(('modified', file_path_str, mtime))
                
                # Also count deleted files
                deleted_files = set(processed_files.keys()) - set(current_files.keys())
                for file_path_str in deleted_files:
                    files_to_process.append(('deleted', file_path_str, None))
                
                # Set count
                currently_processing = len(files_to_process)
                
                # Process files
                for action, file_path_str, mtime in files_to_process:
                    files_being_ingested += 1
                    currently_processing -= 1
                    
                    if action == 'new':
                        print(f"Found new file: {file_path_str}")
                        asyncio.run(ingest_file_async(Path(file_path_str)))
                        processed_files[file_path_str] = mtime
                    elif action == 'modified':
                        print(f"File modified: {file_path_str}")
                        asyncio.run(delete_file_async(Path(file_path_str)))
                        asyncio.run(ingest_file_async(Path(file_path_str)))
                        processed_files[file_path_str] = mtime
                    elif action == 'deleted':
                        print(f"File deleted: {file_path_str}")
                        asyncio.run(delete_file_async(Path(file_path_str)))
                        del processed_files[file_path_str]
                    
                    files_being_ingested -= 1
                
        except Exception as e:
            print(f"Watch error: {e}")
        
        time.sleep(10)

@router.post("/start")
async def start_watching(directory: str):
    global watcher_thread, stop_watching
    
    if watcher_thread and watcher_thread.is_alive():
        return {"status": "already_watching"}
    
    Path(directory).mkdir(parents=True, exist_ok=True)
    
    stop_watching = False
    watcher_thread = threading.Thread(target=watch_directory, args=(directory,))
    watcher_thread.daemon = True
    watcher_thread.start()
    
    return {"status": "started", "watching": directory}

@router.post("/stop")
async def stop_watching_endpoint():
    global stop_watching, watching_directory, currently_processing, files_being_ingested
    stop_watching = True
    watching_directory = None
    currently_processing = 0
    files_being_ingested = 0
    return {"status": "stopped"}

@router.get("/status")
async def get_status():
    global watcher_thread, processed_files, watching_directory, currently_processing, files_being_ingested
    
    is_watching = watcher_thread.is_alive() if watcher_thread else False
    
    return {
        "watching": is_watching,
        "directory": watching_directory if is_watching else None,
        "tracked_files": len(processed_files) if is_watching else 0,
        "currently_processing": currently_processing if is_watching else 0,
        "files_being_ingested": files_being_ingested if is_watching else 0
    }