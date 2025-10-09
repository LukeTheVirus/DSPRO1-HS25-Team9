from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from typing import List
import os

app = FastAPI(title="Embedding Service")

model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
model = None

@app.on_event("startup")
async def load_model():
    global model
    model = SentenceTransformer(model_name)
    print(f"Loaded embedding model: {model_name}")

class EmbedRequest(BaseModel):
    text: str

class BatchEmbedRequest(BaseModel):
    texts: List[str]

@app.get("/health")
async def health():
    return {"status": "healthy", "model": model_name, "loaded": model is not None}

@app.post("/embed")
async def embed_text(request: EmbedRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    embedding = model.encode(request.text).tolist()
    return {"embedding": embedding}

@app.post("/embed/batch")
async def embed_batch(request: BatchEmbedRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    embeddings = model.encode(request.texts).tolist()
    return {"embeddings": embeddings}
