import os
import pytest
from unittest.mock import patch, MagicMock

# Import the workflow to be tested
from services.backend.src.workflows.default.langfuse_test_workflow import langfuse_test

# Check for Langfuse credentials and skip the test if they are not present
langfuse_credentials_present = all(
    os.getenv(k) for k in ["LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
)

pytestmark = pytest.mark.skipif(
    not langfuse_credentials_present,
    reason="Langfuse environment variables are not set. Skipping Langfuse integration tests."
)

@pytest.fixture
def mock_llm_for_langfuse_test():
    """Fixture for a mocked LLM to isolate the Langfuse API call."""
    llm = MagicMock()
    llm.invoke.return_value.content = "Mocked LLM response for Langfuse integration test"
    return llm


@pytest.mark.integration
@patch('services.backend.src.workflows.default.langfuse_test_workflow.create_llm')
def test_langfuse_workflow_integration(mock_create_llm, mock_llm_for_langfuse_test, ollama_config):
    """
    Integration test for the langfuse_test workflow that makes a real call to the Langfuse API.

    This test will:
    1. Authenticate with Langfuse using your environment variables.
    2. Fetch a prompt named "test" from your Langfuse project.
    3. Use a mocked LLM to avoid making a real call to Ollama.
    """
    # Setup the mock LLM
    mock_create_llm.return_value = mock_llm_for_langfuse_test

    # Call the workflow. This will make a real call to Langfuse.
    result = langfuse_test("This is an integration test for Langfuse.", config=ollama_config)

    # Assertions
    assert isinstance(result, str)
    assert result == "Mocked LLM response for Langfuse integration test"

    # Verify that the LLM was created and invoked
    mock_create_llm.assert_called_once()
    mock_llm_for_langfuse_test.invoke.assert_called_once()