import uuid
import hashlib
from datetime import datetime
from qdrant_client.models import PointStruct
from fastapi import APIRouter, UploadFile, File
from ...container import Container
from ...services.qdrant_service import QdrantService, DOCUMENTS_COLLECTION
from ...services.unstructured_service import UnstructuredService
from ...services.embedding_service import EmbeddingService


class IngestionRouter(APIRouter):
    def __init__(self, container: Container, **kwargs):
        super().__init__(**kwargs)
        self._container = container

        self.post("/file")(self.ingest_file)

    async def ingest_file(self, file: UploadFile = File(...), source_path: str = None):
        qdrant_service = self._container.resolve(QdrantService)
        
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        
        qdrant = await qdrant_service.get_client()
        
        documents, _ = await qdrant.scroll(
            collection_name=DOCUMENTS_COLLECTION,
            scroll_filter={"must": [
                {"key": "file_hash", "match": {"value": file_hash}}
            ]},
            limit=1
        )

        if documents:
            return {
                "filename": file.filename,
                "status": "already_processed",
                "hash": file_hash
            }

        unstructured_service = self._container.resolve(UnstructuredService)
        embedding_service = self._container.resolve(EmbeddingService)
        
        parsed_document = await unstructured_service.parse_document(file.filename, file.content_type, content)
        chunks = parsed_document.get("chunks", [])

        embeddings = await embedding_service.embed_texts([chunk["text"] for chunk in chunks])

        points = []
        for chunk, embedding in zip(chunks, embeddings):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "text": chunk["text"],
                        "type": chunk["type"],
                        "filename": file.filename,
                        "source_path": source_path or file.filename,
                        "file_hash": file_hash,
                        "ingested_at": datetime.now().isoformat()
                    }
                )
            )

        await qdrant.upsert(collection_name=DOCUMENTS_COLLECTION, points=points)

        return {
            "filename": file.filename,
            "chunks_processed": len(chunks),
            "status": "success",
            "hash": file_hash
        }