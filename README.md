# RAG System with Docker and Ollama

This project implements a Retrieval-Augmented Generation (RAG) system using a microservices architecture, orchestrated with Docker Compose. It's designed to process documents, store them in a vector database, and use a large language model to answer questions based on the ingested content.

## Architecture

The system is composed of several services that work together:

* **Backend**: A FastAPI application that serves as the main API. It handles file watching and generative Q&A requests.

* **Qdrant**: A vector database used to store document embeddings for efficient similarity searches.

* **Ollama**: Provides the large language model (LLM) for generation. This service is configured to automatically pull the `llama3:8b` model on startup.

* **Embeddings**: A service that uses sentence-transformers to generate vector embeddings for text chunks.

* **Unstructured**: A service for parsing and chunking various document formats.

## Features

* **Automatic File Ingestion**: A file watcher monitors a directory for new or modified files and automatically processes, chunks, and stores them in the vector database.

* **Robust RAG Pipeline**: Implements an advanced RAG workflow:

  1. **Query Expansion**: The user's query is first sent to the LLM to generate a hypothetical, detailed answer.

  2. **Semantic Search**: This expanded query is embedded and used to search the vector database.

  3. **Context Enrichment**: The service retrieves the top 5 unique documents (above a confidence threshold) and fetches all relevant neighboring chunks for each.

* **Generative Q&A**: Generates answers based on the enriched context. The API response includes the final answer, the generated search query, and a rich context object for easy debugging.

* **Health Checks**: Endpoints to monitor the status of all services.

## Getting Started

Follow these steps to get the project up and running.

### Prerequisites

* Docker

* Docker Compose

### Setup

1. **Clone the repository:**

   ```bash
   git clone <your-repository-url>
   cd DSPRO1-HS25-Team9
   ```

2. **Build and Run the Services:**
   This command will build the custom images and start all services in the background.

   ```bash
   docker compose up -d --build
   ```

## Usage

Once the services are running, you can interact with the backend API.

### 1. Start the File Watcher

To begin ingesting files, you must start the watcher. This tells the backend to monitor the `uploads` directory (which is mapped to `./data/uploads`).

```bash
curl -X POST "http://localhost:8000/watch/start?directory=/app/uploads" | jq
```

Any files you add to `./data/uploads` on your host machine will now be automatically processed.

### 2. Generate a Response

This is the main endpoint for asking questions. It uses a `POST` request and expects a JSON body.

```bash
curl -s -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
      "query": "What is Nomad?"
  }' | jq
```

The response will be a JSON object containing the answer and the context used:

```json
{
  "final_answer": "According to the provided context, Nomad is a flexible workload orchestrator...",
  "generated_search_query": "Nomad is an open-source, distributed, and highly available cluster orchestrator...",
  "retrieved_context": {
    "/app/uploads/docs/what-is-nomad.mdx": {
      "text_content": "# Introduction to Nomad\nWelcome to the intro guide...",
      "best_score": 0.612345,
      "retrieved_chunks": 5
    },
    "/app/uploads/docs/use-cases.mdx": {
      "text_content": "# Use Cases\n## Docker container orchestration...",
      "best_score": 0.589123,
      "retrieved_chunks": 3
    }
  }
}
```

### 3. Health Check

To check the status of all services, use the health check endpoint:

```bash
curl http://localhost:8000/health | jq
```

## Testing

The unit and integration tests for the backend service can be found in `services/backend/tests`. For detailed instructions on how to run the tests, please refer to the README in that directory.