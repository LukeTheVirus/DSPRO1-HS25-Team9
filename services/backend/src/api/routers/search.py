from fastapi import APIRouter

from ...container import Container
from ...services.embedding_service import EmbeddingService
from ...services.qdrant_service import QdrantService, DOCUMENTS_COLLECTION


class SearchRouter(APIRouter):
    def __init__(self, container: Container, **kwargs):
        super().__init__(**kwargs)
        self._container = container

        self.get("")(self.search_documents)

    async def search_documents(self, query: str, limit: int = 5):
        embedding_service = self._container.resolve(EmbeddingService)
        qdrant_service = self._container.resolve(QdrantService)

        query_embedding = (await embedding_service.embed_texts([query]))[0]

        qdrant = await qdrant_service.get_client()

        results = await qdrant.search(
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
