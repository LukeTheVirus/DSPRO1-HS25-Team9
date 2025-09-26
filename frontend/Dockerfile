# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

# Prevents Python from writing .pyc files & enables stdout flush
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create a non-root user
RUN useradd -m appuser
WORKDIR /app

# System deps (just what Streamlit needs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# Install python deps first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app
COPY . .

# Switch user
USER appuser

# Expose Streamlit default port
EXPOSE 8501

# Healthcheck (simple TCP)
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD bash -c '</dev/tcp/127.0.0.1/8501' || exit 1

# Run
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

