import pytest
from unittest.mock import patch, MagicMock

from services.backend.src.workflows.default.langfuse_test_workflow import langfuse_test

@pytest.fixture
def mock_llm():
    """Fixture for a mocked LLM."""
    llm = MagicMock()
    llm.invoke.return_value.content = "This is a response from the langfuse test workflow"
    return llm

@pytest.fixture
def mock_langfuse_client():
    """Fixture for a mocked Langfuse client."""
    return MagicMock()

@pytest.fixture
def mock_prompt_template():
    """Fixture for a mocked prompt template."""
    return MagicMock()

# Update patch targets to use absolute paths
@patch('services.backend.src.workflows.default.langfuse_test_workflow.get_messages')
@patch('services.backend.src.workflows.default.langfuse_test_workflow.build_langfuse_prompt')
@patch('services.backend.src.workflows.default.langfuse_test_workflow.langfuse.get_client')
@patch('services.backend.src.workflows.default.langfuse_test_workflow.create_llm')
def test_langfuse_workflow(mock_create_llm, mock_get_client, mock_build_prompt, mock_get_messages, mock_llm, mock_langfuse_client, mock_prompt_template, ollama_config):
    """
    Test the langfuse_test workflow.
    """
    # Setup mocks
    mock_create_llm.return_value = mock_llm
    mock_get_client.return_value = mock_langfuse_client
    mock_build_prompt.return_value = mock_prompt_template
    mock_get_messages.return_value = ["message1", "message2"]

    # Call the workflow
    result = langfuse_test("What is the capital of Switzerland?", config=ollama_config)

    # Assertions
    mock_create_llm.assert_called_once_with(ollama_config)
    mock_get_client.assert_called_once()
    mock_build_prompt.assert_called_once_with("test", mock_langfuse_client, "production")
    mock_get_messages.assert_called_once()
    mock_llm.invoke.assert_called_once_with(["message1", "message2"])
    assert result == "This is a response from the langfuse test workflow"