from qdrant_client.models import Filter, FieldCondition, MatchValue
from pathlib import Path
from fastapi import APIRouter, status
from ...container import Container
from ...services.qdrant_service import QdrantService, DOCUMENTS_COLLECTION


class DeleteRouter(APIRouter):
    def __init__(self, container: Container, **kwargs):
        super().__init__(**kwargs)
        self._container = container

        self.delete("/by-path")(self.delete_by_path)
        self.delete("/by-hash")(self.delete_by_hash)

    async def delete_by_path(self, source_path: str):
        """Delete all chunks from a specific file path"""
        qdrant_service = self._container.resolve(QdrantService)
        qdrant = await qdrant_service.get_client()
        
        # Just delete by filename since that's what's actually stored
        filename = Path(source_path).name
        
        try:
            await qdrant.delete(
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
        except Exception as e:
            print(f"Delete operation error: {e}")
            return {"status": "error"}
        
        return {"status": "success"}

    async def delete_by_hash(self, file_hash: str):
        """Delete all chunks from a specific file hash"""
        qdrant_service = self._container.resolve(QdrantService)
        qdrant = await qdrant_service.get_client()
        
        try:
            await qdrant.delete(
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
        except Exception as e:
            print(f"Delete operation error: {e}")
            return {"status": "error"}

        return {"status": "success"}