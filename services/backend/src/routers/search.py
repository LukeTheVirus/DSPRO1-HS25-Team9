from typing import Annotated
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from ..services.embedding_service import EmbeddingService
from ..services.qdrant_service import QdrantService, DOCUMENTS_COLLECTION
from ..container import Container

router = APIRouter()

@router.get("")
@inject
async def search_documents(
        embedding_service: Annotated[EmbeddingService, Depends(Provide[Container.embedding_service])],
        qdrant_service: Annotated[QdrantService, Depends(Provide[Container.qdrant_service])],
        query: str,
        limit: int = 5,
    ):
    query_embedding = await embedding_service.embed_texts([query])

    qdrant = qdrant_service.get_client()
    
    results = qdrant.search(
        collection_name=DOCUMENTS_COLLECTION,
        query_vector=query_embedding,
        limit=limit
    )
    
    hits = []
    for result in results:
        hits.append({
            "text": result.payload.get("text"),
            "score": result.score,
            "type": result.payload.get("type"),
            "filename": result.payload.get("filename")
        })
    
    return {"query": query, "results": hits}
