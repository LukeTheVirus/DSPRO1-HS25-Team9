from fastapi import APIRouter, HTTPException
from qdrant_client import QdrantClient
import os

router = APIRouter()

@router.delete("/by-path")
async def delete_by_path(source_path: str):
    """Delete all chunks from a specific file path"""
    qdrant = QdrantClient(
        host=os.getenv("QDRANT_HOST", "qdrant"),
        port=int(os.getenv("QDRANT_PORT", 6333))
    )
    
    # Check if documents exist
    existing = qdrant.scroll(
        collection_name="documents",
        scroll_filter={
            "must": [
                {"key": "source_path", "match": {"value": source_path}}
            ]
        },
        limit=1
    )
    
    if not existing[0]:
        raise HTTPException(status_code=404, detail=f"No documents found with path: {source_path}")
    
    # Delete all points with this source_path
    qdrant.delete(
        collection_name="documents",
        points_selector={
            "filter": {
                "must": [
                    {"key": "source_path", "match": {"value": source_path}}
                ]
            }
        }
    )
    
    return {
        "deleted": source_path,
        "status": "success"
    }

@router.delete("/by-hash")
async def delete_by_hash(file_hash: str):
    """Delete all chunks from a specific file hash"""
    qdrant = QdrantClient(
        host=os.getenv("QDRANT_HOST", "qdrant"),
        port=int(os.getenv("QDRANT_PORT", 6333))
    )
    
    # Delete all points with this hash
    qdrant.delete(
        collection_name="documents",
        points_selector={
            "filter": {
                "must": [
                    {"key": "file_hash", "match": {"value": file_hash}}
                ]
            }
        }
    )
    
    return {
        "deleted_hash": file_hash,
        "status": "success"
    }

@router.get("/list")
async def list_documents():
    """List all unique documents in the collection"""
    qdrant = QdrantClient(
        host=os.getenv("QDRANT_HOST", "qdrant"),
        port=int(os.getenv("QDRANT_PORT", 6333))
    )
    
    # Get all documents
    results = qdrant.scroll(
        collection_name="documents",
        limit=10000
    )
    
    # Extract unique documents
    documents = {}
    for point in results[0]:
        path = point.payload.get("source_path")
        if path and path not in documents:
            documents[path] = {
                "filename": point.payload.get("filename"),
                "hash": point.payload.get("file_hash"),
                "ingested_at": point.payload.get("ingested_at")
            }
    
    return {"documents": documents, "total": len(documents)}