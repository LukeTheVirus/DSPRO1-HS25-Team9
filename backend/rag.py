import os
from typing import List, Tuple
import httpx
import chromadb
from chromadb.config import Settings

# Env
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text:latest")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "/data/chroma")

# Chroma client/collection (persistiert auf Volume)
client = chromadb.PersistentClient(
    path=CHROMA_PERSIST_DIR,
    settings=Settings(anonymized_telemetry=False)
)
collection = client.get_or_create_collection("docs")

async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Holt Embeddings von Ollama (ein Text pro Request)."""
    out: List[List[float]] = []
    async with httpx.AsyncClient(timeout=60.0) as s:
        for t in texts:
            r = await s.post(f"{OLLAMA_URL}/api/embeddings", json={
                "model": EMBED_MODEL,
                "input": t
            })
            r.raise_for_status()
            data = r.json()
            # Ollama returns {"embedding": [...]} for single input
            out.append(data["embedding"])
    return out

async def ingest(docs: List[Tuple[str, str]]) -> int:
    """docs: Liste aus (doc_id, content) → upsert nach Chroma."""
    ids = [i for i, _ in docs]
    contents = [c for _, c in docs]
    vectors = await embed_texts(contents)
    collection.upsert(ids=ids, documents=contents, embeddings=vectors)
    return len(ids)

async def retrieve(query: str, k: int = 4) -> List[str]:
    """Top-k Dokumente per Vektor-Suche zurückgeben."""
    qvec = (await embed_texts([query]))[0]
    res = collection.query(query_embeddings=[qvec], n_results=k, include=["documents"])
    return (res.get("documents") or [[]])[0]

