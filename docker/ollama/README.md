# Ollama + Mistral + Open WebUI (Docker Compose)

This stack runs:
- **Ollama** (LLM server) on **port 11434**
- **Open WebUI** (web chat UI) on **port 3000**
- A one-shot helper container to **pre-pull the `mistral` model**

Models are stored in a **persistent Docker volume** so they survive container restarts.

---

## Files

- `docker-compose.yml` — services and volumes (see below)

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports: ["11434:11434"]
    volumes:
      - ollama:/root/.ollama
    healthcheck:
      test: ["CMD", "/bin/sh", "-lc", "ollama list >/dev/null 2>&1"]
      interval: 10s
      timeout: 6s
      retries: 20
    gpus: all

  pull-mistral:
    image: ollama/ollama:latest
    depends_on:
      ollama:
        condition: service_healthy
    environment:
      - OLLAMA_HOST=http://ollama:11434
    volumes:
      - ollama:/root/.ollama
    entrypoint: ["/bin/sh","-lc","ollama pull mistral"]

  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: openwebui
    ports: ["3000:8080"]
    depends_on:
      - ollama
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_API_BASE=http://ollama:11434
    volumes:
      - openwebui:/app/backend/data

volumes:
  ollama:
  openwebui:
```

---

## What each service does

### `ollama`
- Runs `ollama serve` and exposes the HTTP API on `11434`.
- Mounts the `ollama` volume at `/root/.ollama` (where models & cache live).
- Healthcheck uses `ollama list` (no `curl` required).
- `gpus: all` enables NVIDIA GPU if the NVIDIA Container Toolkit is installed.

### `pull-mistral`
- Waits for `ollama` to become healthy, then runs `ollama pull mistral`.
- Shares the same `ollama` volume so the model is persisted.
- Exits after the pull completes.

### `openwebui`
- Web interface for Ollama on `http://localhost:3000`.
- Talks to Ollama via the compose **service name** (`http://ollama:11434`).
- Persists its own data (users, chats, settings) in the `openwebui` volume.

---

## Prerequisites

- **Docker** and **Docker Compose** installed in your environment.
- For **GPU acceleration**:
  - NVIDIA driver on the host.
  - Inside Linux/WSL: **NVIDIA Container Toolkit** installed and configured:
    - `sudo apt install -y nvidia-container-toolkit`
    - `sudo nvidia-ctk runtime configure --runtime=docker`
    - `sudo systemctl restart docker`
  - Verify with:  
    `docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi`

> CPU-only works too; if you don’t have GPU support, remove the `gpus: all` line.

---

## Usage

### Start (watch logs interactively)
```
docker compose up
```

### Start in background
```
docker compose up -d
```

### Check logs
```
docker compose logs -f            # all services
docker compose logs -f ollama     # just the server
docker compose logs -f pull-mistral
docker compose logs -f openwebui
```

### Stop / Start / Recreate
```
docker compose stop
docker compose start
docker compose down
```

### Update to latest images
```
docker compose pull
docker compose up -d
```

---

## Endpoints

- **Open WebUI:** http://localhost:3000  
  First visit will prompt you to create an admin user.

- **Ollama API:** http://localhost:11434  
  Quick checks:
  ```
  curl http://localhost:11434/api/version
  curl http://localhost:11434/api/tags
  ```

- **Test generation:**
  ```
  curl http://localhost:11434/api/generate -d '{
    "model":"mistral",
    "prompt":"Say hello in one short sentence."
  }'
  ```

---

## Managing models

List models:
```
docker exec -it ollama ollama list
```

Pull another model (examples):
```
docker exec -it ollama ollama pull llama3.1
docker exec -it ollama ollama pull mistral-nemo
```

Remove a model:
```
docker exec -it ollama ollama rm mistral
```

> Models are stored in the **`ollama`** volume (inside container at `/root/.ollama`, on host under Docker’s volume path). They persist across container restarts.  
> **Warning:** `docker compose down -v` deletes containers **and volumes** (models and Open WebUI data).

---

## Troubleshooting

- **Open WebUI shows no models**
  - Make sure the model pull completed: `docker exec -it ollama ollama list`
  - Ensure `OLLAMA_API_BASE` and `OLLAMA_BASE_URL` in `openwebui` service are set to `http://ollama:11434`

