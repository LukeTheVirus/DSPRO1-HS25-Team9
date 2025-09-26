```
docker build -t chatbot-frontend .
docker run --rm -p 8501:8501   --add-host=host.docker.internal:host-gateway   -e BACKEND_URL=http://host.docker.internal:11434   -e MODEL=mistral:latest   chatbot-frontend
```
