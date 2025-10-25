#!/bin/bash
set -e

PROJECT_ROOT="/opt/rag_it"
REPO_DIR="$(pwd)"

# Create directories in /opt
echo "Creating directories in $PROJECT_ROOT..."
sudo mkdir -p "$PROJECT_ROOT"/data/{qdrant,ollama,uploads,processing}
sudo mkdir -p "$PROJECT_ROOT"/logs
sudo chown -R "$USER:$USER" "$PROJECT_ROOT"

# Copy all services
echo "Copying services..."
cp -r "$REPO_DIR/services" "$PROJECT_ROOT/"

echo "Copying frontend..."
cp -r "$REPO_DIR/frontend" "$PROJECT_ROOT/"

# Copy docker-compose
echo "Copying docker-compose.yml..."
cp "$REPO_DIR/docker-compose.yml" "$PROJECT_ROOT/"

# Go to project root
cd "$PROJECT_ROOT"

# Build images
echo "Building containers..."
docker compose build

# Start services
echo "Starting services..."
docker compose up -d

# --- Automatically pull required models ---
echo "Pulling Ollama models... (this may take a few minutes)"

# Use the service name 'rag_it_ollama' from docker-compose.yml
docker compose exec rag_it_ollama ollama pull gpt-oss:20b
docker compose exec rag_it_ollama ollama pull mistral
docker compose exec rag_it_ollama ollama pull qwen3:30b
docker compose exec rag_it_ollama ollama pull qwen3-coder:30b

echo "Ollama models are ready!"

# Wait and check
sleep 10
echo "Checking health..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Backend not ready yet"

echo ""
echo "Setup complete!"
echo "Services running from: $PROJECT_ROOT"
echo "  - Backend: http://localhost:8000"
echo "  - Embeddings: http://localhost:8001"
echo "  - Qdrant: http://localhost:6333"
echo "  - Ollama: http://localhost:11434"
echo "  - Frontend: http://localhost:8501"
echo ""
echo "Logs: cd $PROJECT_ROOT && docker compose logs -f"

echo "to pull a model (e.g. mistral), run: docker exec -it rag_it_ollama ollama pull mistral"
