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
    global stop_watching
    
    processed = {}  # Track files with modification time: {path: mtime}
    
    while not stop_watching:
        try:
            path = Path(directory)
            if path.exists():
                # Find all current files with their modification times
                current_files = {}
                for ext in SUPPORTED_EXTENSIONS:
                    for file_path in path.glob(f"*{ext}"):
                        current_files[str(file_path)] = file_path.stat().st_mtime
                
                # Find new or modified files
                for file_path_str, mtime in current_files.items():
                    if file_path_str not in processed:
                        # New file
                        print(f"Found new file: {file_path_str}")
                        asyncio.run(ingest_file_async(Path(file_path_str)))
                        processed[file_path_str] = mtime
                    elif processed[file_path_str] < mtime:
                        # Modified file
                        print(f"File modified: {file_path_str}")
                        asyncio.run(ingest_file_async(Path(file_path_str)))
                        processed[file_path_str] = mtime
                
                # Find deleted files
                deleted_files = set(processed.keys()) - set(current_files.keys())
                for file_path_str in deleted_files:
                    print(f"File deleted: {file_path_str}")
                    asyncio.run(delete_file_async(Path(file_path_str)))
                    del processed[file_path_str]
                
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
    global stop_watching
    stop_watching = True
    return {"status": "stopped"}

@router.get("/status")
async def get_status():
    global watcher_thread
    return {
        "watching": watcher_thread.is_alive() if watcher_thread else False
    }