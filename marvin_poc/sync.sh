#!/bin/bash
set -e

PROJECT_ROOT="/opt/rag_it"
REPO_DIR="$(pwd)"

echo "Syncing files to $PROJECT_ROOT..."

# Sync backend source
rsync -av --delete \
  "$REPO_DIR/services/backend/src/" \
  "$PROJECT_ROOT/services/backend/src/"

# Sync embeddings source
rsync -av --delete \
  "$REPO_DIR/services/embeddings/src/" \
  "$PROJECT_ROOT/services/embeddings/src/"

# Sync unstructured source
rsync -av --delete \
  "$REPO_DIR/services/unstructured/src/" \
  "$PROJECT_ROOT/services/unstructured/src/"

# Sync unstructured source
rsync -av --delete \
  "$REPO_DIR/docker-compose.yml" \
  "$PROJECT_ROOT/docker-compose.yml"
  
echo "Sync complete!"
