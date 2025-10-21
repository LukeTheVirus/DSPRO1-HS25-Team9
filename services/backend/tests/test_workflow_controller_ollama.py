import pytest
from unittest.mock import patch, MagicMock

# Import the workflow controller
from workflows.workflow_controller import call_workflow


@pytest.fixture
def mock_llm():
    """Fixture for a mocked LLM."""
    llm = MagicMock()
    llm.invoke.return_value = "This is a response from Ollama model"
    return llm


@pytest.fixture
def mock_prompt_template():
    """Fixture for a mocked prompt template."""
    return MagicMock()


@pytest.fixture
def mock_messages():
    """Fixture for mocked messages."""
    return ["message1", "message2"]


@patch('services.backend.src.workflows.default.workflow.create_llm')
@patch('services.backend.src.workflows.default.workflow.get_messages')
def test_call_workflow_with_ollama(mock_get_messages, mock_create_llm, ollama_config, mock_llm, mock_messages):
    """
    Test calling the default workflow with Ollama model.
    """
    # Setup mocks
    mock_create_llm.return_value = mock_llm
    mock_get_messages.return_value = mock_messages

    # Call the workflow controller with Ollama config
    result = call_workflow("What is machine learning?", config=ollama_config)

    # Assertions
    mock_create_llm.assert_called_once()
    mock_get_messages.assert_called_once()
    mock_llm.invoke.assert_called_once_with(mock_messages)
    assert result == "This is a response from Ollama model"


@patch('services.backend.src.workflows.default.workflow.create_llm')
@patch('services.backend.src.workflows.default.workflow.get_messages')
def test_call_workflow_with_ollama_different_model(mock_get_messages, mock_create_llm, ollama_config_mistral, mock_messages):
    """
    Test calling the default workflow with a different Ollama model.
    """
    # Setup mocks
    # Create a different mock_llm for this test with a different response
    mock_llm_different = MagicMock()
    mock_llm_different.invoke.return_value = "This is a response from a different Ollama model"
    mock_create_llm.return_value = mock_llm_different

    mock_get_messages.return_value = mock_messages

    # Call the workflow controller with Ollama config for mistral model
    result = call_workflow("Explain quantum computing", config=ollama_config_mistral)

    # Assertions
    mock_create_llm.assert_called_once()
    mock_get_messages.assert_called_once()
    mock_llm_different.invoke.assert_called_once_with(mock_messages)
    assert result == "This is a response from a different Ollama model"