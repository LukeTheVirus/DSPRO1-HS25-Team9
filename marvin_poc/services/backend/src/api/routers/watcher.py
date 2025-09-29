from fastapi import APIRouter
from pathlib import Path
import asyncio
import httpx
import threading

router = APIRouter()

# Global state
watcher_thread = None
stop_watching = False

SUPPORTED_EXTENSIONS = {
    '.pdf', '.txt', '.docx', '.doc', '.pptx', '.ppt',
    '.html', '.xml', '.json', '.csv', '.md', '.rtf',
    '.epub', '.msg', '.eml'
}

def watch_directory(directory: str):
    """Simple blocking watcher in a thread"""
    global stop_watching
    processed = set()
    
    while not stop_watching:
        try:
            path = Path(directory)
            if path.exists():
                for ext in SUPPORTED_EXTENSIONS:
                    for file_path in path.glob(f"*{ext}"):
                        if str(file_path) not in processed:
                            print(f"Found new file: {file_path}")
                            # Mark as processed immediately
                            processed.add(str(file_path))
                            # TODO: Add actual ingestion call here
        except Exception as e:
            print(f"Watch error: {e}")
        
        import time
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