import os
import pytest

# Import the workflow controller
from services.backend.src.workflow_controller import call_workflow

# Skip all tests in this module if the environment variable is not set.
pytestmark = pytest.mark.skipif(not os.getenv("OLLAMA_SERVICE_URL"), reason="OLLAMA_SERVICE_URL environment variable is not set. Skipping integration tests.")


@pytest.mark.integration
def test_call_workflow_with_ollama_qwen_integration(ollama_config_qwen):
    """
    Integration test for calling the default workflow with the qwen3:30b Ollama model.
    """

    # Call the workflow controller with the qwen model config
    result = call_workflow("Explain the significance of the Magna Carta in the context of modern law.", config=ollama_config_qwen)

    # Assertions
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0