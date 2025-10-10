import uvicorn

from .api.api import Api
from .container import Container
from .services.service_module import ServiceModule


def _setup_container():
    container = Container()
    container.load_module(ServiceModule)
    return container


def main():
    container = _setup_container()

    app = Api(container)

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    print("Starting RAG MVP Backend...")
    main()
