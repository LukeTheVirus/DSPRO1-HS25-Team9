import uvicorn
from .api import Api
from .container import Container

if __name__ == "__main__":
    print("Starting RAG MVP Backend...")
    container = Container()
    api = Api(container)
    app = api.get_app()

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        print("Shutting down RAG MVP Backend...")