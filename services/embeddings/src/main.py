from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from typing import List
import os
import torch  # <-- Add this import

app = FastAPI(title="Embedding Service")

model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
model = None


@app.on_event("startup")
async def load_model():
    global model

    local_model_path = f"/app/{model_name}"

    # --- Start of new device logic ---
    device_to_use = "cpu"  # Default to CPU
    try:
        if torch.cuda.is_available():
            device_to_use = "cuda"  # Default to CUDA if available
            gpu_name = torch.cuda.get_device_name(0)
            print(f"Found GPU: {gpu_name}")

            # Check for the specific problematic GPU
            if "5090" in gpu_name:
                print("WARNING: Found RTX 5090. This GPU may be incompatible with the container's PyTorch build.")
                print("Forcing CPU execution to prevent potential CUDA errors.")
                device_to_use = "cpu"
        else:
            print("No CUDA-compatible GPU found. Using CPU.")
    except Exception as e:
        print(f"Error during GPU detection: {e}. Defaulting to CPU.")
        device_to_use = "cpu"
    # --- End of new device logic ---

    try:
        # 1. Try to load from the local path first
        if os.path.isdir(local_model_path):
            print(f"Loading embedding model from local path: {local_model_path}")
            model = SentenceTransformer(local_model_path, device=device_to_use)

        # 2. If local path doesn't exist, fall back to downloading
        else:
            print(f"Local model not found at '{local_model_path}'.")
            print(f"Attempting to download model: {model_name}")
            model = SentenceTransformer(model_name, device=device_to_use)

        print(f"Model loaded successfully on device: {device_to_use}")

    except Exception as e:
        print(f"CRITICAL: Failed to load embedding model.")
        print(f"Local path check: '{local_model_path}' (Not found or failed)")
        print(f"Download attempt: '{model_name}' (Failed)")
        print(f"Error: {e}")


class EmbedRequest(BaseModel):
    text: str


class BatchEmbedRequest(BaseModel):
    texts: List[str]


@app.get("/health")
async def health():
    model_loaded = model is not None
    status = "healthy" if model_loaded else "degraded"
    return {"status": status, "model": model_name, "loaded": model_loaded}


@app.post("/embed")
async def embed_text(request: EmbedRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded. Check service logs.")

    embedding = model.encode(request.text).tolist()
    return {"embedding": embedding}


@app.post("/embed/batch")
async def embed_batch(request: BatchEmbedRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded. Check service logs.")

    embeddings = model.encode(request.texts).tolist()
    return {"embeddings": embeddings}