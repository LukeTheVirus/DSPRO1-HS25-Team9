from typing import Annotated
from qdrant_client.models import Filter, FieldCondition, MatchValue
from pathlib import Path
from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject
from ..container import Container
from ..services.qdrant_service import QdrantService, DOCUMENTS_COLLECTION

router = APIRouter()

@router.delete("/by-path")
@inject
async def delete_by_path(source_path: str, qdrant_service: Annotated[QdrantService, Depends(Provide[Container.qdrant_service])]):
    """Delete all chunks from a specific file path"""
    qdrant = qdrant_service.get_client()
    
    # Just delete by filename since that's what's actually stored
    filename = Path(source_path).name
    
    try:
        # Delete all points with this filename using proper Filter syntax
        qdrant.delete(
            collection_name=DOCUMENTS_COLLECTION,
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
async def delete_by_hash(file_hash: str, qdrant_service: Annotated[QdrantService, Depends(Provide[Container.qdrant_service])]):
    """Delete all chunks from a specific file hash"""
    qdrant = qdrant_service.get_client()
    
    # Delete using proper Filter syntax
    qdrant.delete(
        collection_name=DOCUMENTS_COLLECTION,
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