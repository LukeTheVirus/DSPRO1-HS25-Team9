import os
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams


DOCUMENTS_COLLECTION = "documents"

class QdrantService:
    
    def __init__(self):
        self._initialized = False
        self._client = AsyncQdrantClient(
            host=os.getenv("QDRANT_HOST", "qdrant"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
        
    async def initialize(self):
        if self._initialized:
            raise Exception("QdrantService is already initialized.")
        print("Initializing QdrantService...")
        self._initialized = True
        await self._setup_db()
        
    def get_client(self) -> AsyncQdrantClient:
        self._validate_initialized()
        return self._client
            
    async def dispose(self):
        print("Disposing QdrantService...")
        self._validate_initialized()
        await self._client.close()
        self._initialized = False

    async def _setup_db(self):
        if not await self._client.collection_exists(DOCUMENTS_COLLECTION):
            await self._client.create_collection(
                collection_name=DOCUMENTS_COLLECTION,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
        
    def _validate_initialized(self):
        if not self._initialized:
            raise Exception("QdrantService is not initialized.")
    