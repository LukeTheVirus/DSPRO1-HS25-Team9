import uvicorn
import asyncio
from .api import Api
from .container import Container

async def start_services():
    container = Container()
    await container.qdrant_service().initialize()
    return container

async def create_app():
    container = await start_services()
    api = Api(container)
    return api.get_app()

def main():
    app = asyncio.run(create_app())
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    print("Starting RAG MVP Backend...")
    main()