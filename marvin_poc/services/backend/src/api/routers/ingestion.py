from fastapi import APIRouter, UploadFile, File
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import httpx
import os
import uuid
import hashlib
from datetime import datetime

router = APIRouter()

@router.post("/file")
async def ingest_file(file: UploadFile = File(...), source_path: str = None):
    # Read file content once
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Check if already processed
    qdrant = QdrantClient(
        host=os.getenv("QDRANT_HOST", "qdrant"),
        port=int(os.getenv("QDRANT_PORT", 6333))
    )
    
    collection_name = "documents"
    
        # Create collection if doesn't exist
    try:
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
        )
    except:
        pass  # Collection already exists
    
    # Search for existing file by hash
    existing = qdrant.scroll(
        collection_name="documents",
        scroll_filter={"must": [
            {"key": "file_hash", "match": {"value": file_hash}}
        ]},
        limit=1
    )
    
    if existing[0]:  # Document already exists
        return {
            "filename": file.filename,
            "status": "already_processed",
            "hash": file_hash
        }
    
    # Step 1: Parse document using content we already read
    async with httpx.AsyncClient(timeout=30.0) as client:
        unstructured_url = os.getenv("UNSTRUCTURED_SERVICE_URL", "http://unstructured:8002")
        files = {"file": (file.filename, content, file.content_type)}
        
        parse_response = await client.post(f"{unstructured_url}/parse", files=files)
        parse_data = parse_response.json()
        
        # Step 2: Get embeddings for each chunk
        embedding_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embeddings:8001")
        chunks = parse_data.get("chunks", [])
        texts = [chunk["text"] for chunk in chunks]
        
        embed_response = await client.post(
            f"{embedding_url}/embed/batch",
            json={"texts": texts}
        )
        embeddings = embed_response.json()["embeddings"]
    
    # Step 3: Store in Qdrant

    
    # Add points with metadata
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
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
    
    qdrant.upsert(collection_name=collection_name, points=points)
    
    return {
        "filename": file.filename,
        "chunks_processed": len(chunks),
        "collection": collection_name,
        "status": "success",
        "hash": file_hash
    }