import os, json
from typing import List, Optional
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import rag  # <- wir importieren das Modul und rufen rag.ingest/rag.retrieve auf

app = FastAPI(title="Chat/RAG Backend")

# CORS für Streamlit
allow_origins = os.getenv("ALLOW_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allow_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
CHAT_MODEL = os.getenv("CHAT_MODEL", "mistral:latest")

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    stream: bool = False
    temperature: Optional[float] = 0.2

class ChatResponse(BaseModel):
    answer: str

class RAGQuery(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = 4
    system_prompt: Optional[str] = (
        "Use the provided context to answer. If the answer is not in the context, say you don't know."
    )

class IngestDoc(BaseModel):
    id: str
    content: str

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Nicht-streamendes Chat-Proxy zu Ollama."""
    payload = {
        "model": CHAT_MODEL,
        "messages": [m.model_dump() for m in req.messages],
        "options": {"temperature": req.temperature},
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=300.0) as s:
        r = await s.post(f"{OLLAMA_URL}/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        content = data.get("message", {}).get("content", "")
        return {"answer": content}

@app.post("/rag/query", response_model=ChatResponse)
async def rag_query(q: RAGQuery):
    """Retrieve → prompten mit Kontext → LLM antworten lassen."""
    ctx_docs = await rag.retrieve(q.query, k=q.k)
    context = "\n\n---\n\n".join(ctx_docs)

    messages = [
        {"role": "system", "content": q.system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {q.query}"},
    ]

    async with httpx.AsyncClient(timeout=300.0) as s:
        r = await s.post(f"{OLLAMA_URL}/api/chat", json={
            "model": CHAT_MODEL,
            "messages": messages,
            "stream": False
        })
        r.raise_for_status()
        data = r.json()
        content = data.get("message", {}).get("content", "")
        return {"answer": content}

@app.post("/ingest")
async def ingest_endpoint(docs: List[IngestDoc]):
    count = await rag.ingest([(d.id, d.content) for d in docs])
    return {"ingested": count}

