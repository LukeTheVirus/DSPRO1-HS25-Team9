from fastapi import APIRouter
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import os
from pathlib import Path

router = APIRouter()

@router.delete("/by-path")
async def delete_by_path(source_path: str):
    """Delete all chunks from a specific file path"""
    qdrant = QdrantClient(
        host=os.getenv("QDRANT_HOST", "qdrant"),
        port=int(os.getenv("QDRANT_PORT", 6333))
    )
    
    # Just delete by filename since that's what's actually stored
    filename = Path(source_path).name
    
    try:
        # Delete all points with this filename using proper Filter syntax
        qdrant.delete(
            collection_name="documents",
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="filename",
                        match=MatchValue(value=filename)
                    )
                ]
            )
        )
        print(f"Deleted all chunks for filename: {filename}")
    except Exception as e:
        print(f"Delete operation error: {e}")
    
    return {
        "deleted": source_path,
        "filename": filename,
        "status": "success"
    }

@router.delete("/by-hash")
async def delete_by_hash(file_hash: str):
    """Delete all chunks from a specific file hash"""
    qdrant = QdrantClient(
        host=os.getenv("QDRANT_HOST", "qdrant"),
        port=int(os.getenv("QDRANT_PORT", 6333))
    )
    
    # Delete using proper Filter syntax
    qdrant.delete(
        collection_name="documents",
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="file_hash",
                    match=MatchValue(value=file_hash)
                )
            ]
        )
    )
    
    return {
        "deleted_hash": file_hash,
        "status": "success"
    }