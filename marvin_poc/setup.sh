#!/bin/bash

set -e

PROJECT_ROOT="/opt/rag_it"
REPO_DIR="$(pwd)"

sudo mkdir -p "$PROJECT_ROOT"/{config,data/{qdrant,ollama},logs}
sudo chown -R "$USER:$USER" "$PROJECT_ROOT"

cp "$REPO_DIR/config/"* "$PROJECT_ROOT/config/"
cp "$REPO_DIR/docker-compose.yml" "$PROJECT_ROOT/"

echo "Setup complete. Run: cd $PROJECT_ROOT && docker compose up -d"