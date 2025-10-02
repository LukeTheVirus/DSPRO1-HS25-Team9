from fastapi import FastAPI, UploadFile, File
from unstructured.partition.auto import partition
import tempfile
import os

app = FastAPI(title="Unstructured Service")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/parse")
async def parse_document(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        elements = partition(filename=tmp_path)
        chunks = [{"text": str(el), "type": el.category} for el in elements]
        return {"filename": file.filename, "chunks": chunks}
    finally:
        os.unlink(tmp_path)
