import os
import pytest

# Import the workflow controller
from services.backend.src.workflows.workflow_controller import call_workflow

# Skip all tests in this module if the environment variable is not set.
# This replaces the old setUp method.
pytestmark = pytest.mark.skipif(
    not os.getenv("OLLAMA_SERVICE_URL"),
    reason="OLLAMA_SERVICE_URL environment variable is not set. Skipping integration tests."
)


@pytest.mark.integration
def test_call_workflow_with_ollama_integration(ollama_config):
    """
    Integration test for calling the default workflow with Ollama model.
    """

    # Call the workflow controller with Ollama config
    result = call_workflow("What is machine learning?", config=ollama_config)

    # Assertions (using plain 'assert' instead of 'self.assert...')
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.integration
def test_call_workflow_with_ollama_different_model_integration(ollama_config_mistral):
    """
    Integration test for calling the default workflow with a different Ollama model.
    """

    # Call the workflow controller with Ollama config for mistral model
    result = call_workflow("Explain quantum computing", config=ollama_config_mistral)

    # Assertions
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.integration
def test_call_workflow_with_ollama_qwen_integration(ollama_config_qwen):
    """
    Integration test for calling the default workflow with the qwen3:30b Ollama model.
    """

    # Call the workflow controller with the qwen model config
    result = call_workflow("Explain the significance of the Magna Carta in the context of modern law.",
                           config=ollama_config_qwen)

    # Assertions
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0