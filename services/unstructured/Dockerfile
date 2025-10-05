FROM downloads.unstructured.io/unstructured-io/unstructured:latest

WORKDIR /app

# Install FastAPI for our wrapper
RUN pip install fastapi uvicorn python-multipart

COPY src/ ./src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
