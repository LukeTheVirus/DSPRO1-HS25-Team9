import os

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType


DOCUMENTS_COLLECTION = "documents"
EMBEDDING_VECTOR_SIZE = 1024 
DOCUMENT_IDENTIFIER_FIELD = "identifier" 
DOCUMENT_HASH_FIELD = "hash"


class QdrantService:
    def __init__(self):
        self._initialized = False
        self._client = AsyncQdrantClient(
            host=os.getenv("QDRANT_HOST", "qdrant"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )

    async def get_client(self) -> AsyncQdrantClient:
        await self._validate_initialized()
        return self._client

    async def health_check(self) -> bool:
        response = await self._client.get_collections()
        return any(response.collections)

    async def _validate_initialized(self):
        if not self._initialized:
            await self.initialize()

    async def initialize(self):
        if self._initialized:
            return
        print("Initializing QdrantService...")
        await self._setup_db()
        self._initialized = True

    async def _setup_db(self):
        collection_exists = await self._client.collection_exists(DOCUMENTS_COLLECTION)
        
        if not collection_exists:
            # 1. Create the collection
            await self._client.create_collection(
                collection_name=DOCUMENTS_COLLECTION,
                vectors_config=VectorParams(size=EMBEDDING_VECTOR_SIZE, distance=Distance.COSINE)
            )
            
            # 2. Create the payload index for grouping
            print(f"Creating payload index for: {DOCUMENT_IDENTIFIER_FIELD}")
            await self._client.create_payload_index(
                collection_name=DOCUMENTS_COLLECTION,
                field_name=DOCUMENT_IDENTIFIER_FIELD,
                field_schema=PayloadSchemaType.KEYWORD
            )
            
            # 3. Create the payload index for duplicate checks
            print(f"Creating payload index for: {DOCUMENT_HASH_FIELD}")
            await self._client.create_payload_index(
                collection_name=DOCUMENTS_COLLECTION,
                field_name=DOCUMENT_HASH_FIELD,
                field_schema=PayloadSchemaType.KEYWORD 
            )