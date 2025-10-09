import os
import pytest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load the .env file to populate the environment for the test run
load_dotenv()

from services.backend.src.workflows.default.langfuse_test_workflow import langfuse_test

langfuse_credentials_present = all(
    os.getenv(k) for k in ["LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
)
pytestmark = pytest.mark.skipif(
    not langfuse_credentials_present,
    reason="Langfuse environment variables not set. Skipping Langfuse integration tests."
)

@pytest.fixture
def mock_llm_for_langfuse_test():
    llm = MagicMock()
    llm.invoke.return_value.content = "Mocked LLM response for Langfuse integration test"
    return llm

@pytest.mark.integration
@patch('services.backend.src.workflows.default.langfuse_test_workflow.create_llm')
def test_langfuse_workflow_integration(mock_create_llm, mock_llm_for_langfuse_test, ollama_config):
    """
    Integration test for the langfuse_test workflow.
    """
    mock_create_llm.return_value = mock_llm_for_langfuse_test

    result = langfuse_test("This is an integration test for Langfuse.", config=ollama_config)

    # Assertions
    assert result == "Mocked LLM response for Langfuse integration test"
    mock_create_llm.assert_called_once()
    mock_llm_for_langfuse_test.invoke.assert_called_once()