# RAG System with Docker and Ollama

This project implements a Retrieval-Augmented Generation (RAG) system using a microservices architecture, orchestrated with Docker Compose. It's designed to process documents, store them in a vector database, and use a large language model to answer questions based on the ingested content.

## Architecture

The system is composed of several services that work together:

  * **Backend**: A FastAPI application that serves as the main entry point for the system. It handles requests for document ingestion, searching, and generation.
  * **Qdrant**: A vector database used to store document embeddings for efficient similarity searches.
  * **Ollama**: Provides the large language model (LLM) for generating responses.
  * **Embeddings**: A service that uses sentence-transformers to generate vector embeddings for text chunks.
  * **Unstructured**: A service for parsing and chunking various document formats, including `.pdf`, `.docx`, and `.txt`.

## Features

  * **Document Ingestion**: Upload files to be processed, chunked, and stored in the vector database.
  * **File Watcher**: Automatically monitors a directory for new or modified files and ingests them into the system.
  * **Semantic Search**: Search for relevant document chunks based on a query.
  * **Generative Q\&A**: Generate answers to questions based on the context of the ingested documents.
  * **Health Checks**: Endpoints to monitor the status of all services.

## Getting Started

Follow these steps to get the project up and running.

### Prerequisites

  * Docker
  * Docker Compose

### Setup

1.  **Clone the repository:**

    ```bash
    git clone <your-repository-url>
    cd DSPRO1-HS25-Team9
    ```

2.  **Set up environment variables:**
    Create a `.env` file by copying the example and filling in your Langfuse credentials if you wish to use tracing:

    ```bash
    cp .env.example .env
    ```

3.  **Run the setup script:**
    This script will create the necessary directories and start all the services using Docker Compose.

    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

## Usage

Once the services are running, you can interact with the backend API.

### Start the File Watcher

To automatically ingest files from the `uploads` directory, start the watcher:

```bash
curl -X POST "http://localhost:8000/watch/start?directory=/app/uploads" | jq
```

### Ingest a File Manually

You can also upload a file directly to the ingestion endpoint:

```bash
curl -X POST http://localhost:8000/ingest/file \
  -F "file=@/path/to/your/document.pdf" \
  -F "source_path=/path/to/your/document.pdf" | jq
```

### Search for Documents

Perform a semantic search on the ingested documents:

```bash
curl "http://localhost:8000/search?query=your%20search%20query&limit=5" | jq
```

### Generate a Response

Generate a response from the LLM based on your query:

```bash
curl -X POST "http://localhost:8000/generate?query=your%20question" | jq
```

### Health Check

To check the status of all services, use the health check endpoint:

```bash
curl http://localhost:8000/health | jq
```

## Testing

The unit and integration tests for the backend service can be found in `services/backend/tests`. For detailed instructions on how to run the tests, please refer to the README in that directory.