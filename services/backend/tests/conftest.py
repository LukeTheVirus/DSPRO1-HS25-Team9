import os
import pytest

@pytest.fixture
def ollama_config():
    """
    Fixture that returns a config for Ollama with gpt-oss:20b model.
    """
    return {
        "provider": "ollama",
        "model": "gpt-oss:20b",
        "temperature": 0.7,
        "max_retries": 2
    }

@pytest.fixture
def ollama_config_mistral():
    """
    Fixture that returns a config for Ollama with mistral model.
    """
    return {
        "provider": "ollama",
        "model": "mistral",
        "temperature": 0.5,
        "max_retries": 3
    }

@pytest.fixture
def ollama_config_qwen():
    """
    Fixture that returns a config for Ollama with qwen3:30b model.
    """
    return {
        "provider": "ollama",
        "model": "qwen3:30b",
        "temperature": 0.5,
        "max_retries": 2
    }


def pytest_configure(config):
    """
    Configure pytest.
    """
    config.addinivalue_line("markers", "integration: mark test as an integration test")

def pytest_collection_modifyitems(config, items):
    """
    Skip integration tests if not explicitly requested.
    """
    if not config.getoption("--runintegration"):
        skip_integration = pytest.mark.skip(reason="need --runintegration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

def pytest_addoption(parser):
    """
    Add command line options to pytest.
    """
    parser.addoption(
        "--runintegration",
        action="store_true",
        default=False,
        help="run integration tests"
    )