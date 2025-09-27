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

# Wait and check
sleep 5
echo "Checking health..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Backend not ready yet"

echo ""
echo "Setup complete!"
echo "Services running from: $PROJECT_ROOT"
echo "  - Backend: http://localhost:8000"
echo "  - Embeddings: http://localhost:8001"
echo "  - Qdrant: http://localhost:6333"
echo "  - Ollama: http://localhost:11434"
echo ""
echo "Logs: cd $PROJECT_ROOT && docker compose logs -f"
