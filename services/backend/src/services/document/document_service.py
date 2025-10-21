import hashlib
import uuid
from typing import List

from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct

from .document_data import DocumentData
from .document_result import DocumentResult
from ..external.embedding_service import EmbeddingService
from ..external.qdrant_service import QdrantService, DOCUMENTS_COLLECTION
from ..external.unstructured_service import UnstructuredService


class DocumentService:
    def __init__(self, qdrant_service: QdrantService, embedding_service: EmbeddingService,
                 unstructured_service: UnstructuredService):
        self._qdrant_service = qdrant_service
        self._embedding_service = embedding_service
        self._unstructured_service = unstructured_service

    async def insert_document(self, identifier: str, raw_content: bytes, content_type: str = "text/plain"):
        document_hash = hashlib.sha256(raw_content).hexdigest()

        qdrant = await self._qdrant_service.get_client()

        query_result = await qdrant.query_points(
            collection_name=DOCUMENTS_COLLECTION,
            query_filter=Filter(must=[
                FieldCondition(
                    key="hash",
                    match=MatchValue(value=document_hash)
                )
            ]),
            limit=1
        )

        if len(query_result.points) > 0:
            return False

        parsed_document = await self._unstructured_service.parse_document(content_type, raw_content)
        chunks = parsed_document.get("chunks", [])

        embeddings = await self._embedding_service.embed_texts([chunk["text"] for chunk in chunks])

        points = []
        for chunk, embedding in zip(chunks, embeddings):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "identifier": identifier,
                        "hash": document_hash,
                        "text_content": chunk["text"],
                    }
                )
            )

        await qdrant.upsert(collection_name=DOCUMENTS_COLLECTION, points=points)

        return True

    async def search(self, query: str, limit: int = 5) -> List[DocumentResult]:
        query_embedding = (await self._embedding_service.embed_texts([query]))[0]

        qdrant = await self._qdrant_service.get_client()

        query_result = await qdrant.query_points(DOCUMENTS_COLLECTION, query_embedding, limit=limit)

        hits = []
        for point in query_result.points:
            identifier = point.payload.get("identifier")
            text_content = point.payload.get("text_content")
            hash = point.payload.get("hash")
            document_result = DocumentResult(DocumentData(identifier, hash, text_content), point.score)
            hits.append(document_result)

        return hits

    async def delete_by_identifier(self, identifier: str):
        qdrant = await self._qdrant_service.get_client()

        await qdrant.delete(
            collection_name=DOCUMENTS_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="identifier",
                        match=MatchValue(value=identifier)
                    )
                ]
            )
        )
