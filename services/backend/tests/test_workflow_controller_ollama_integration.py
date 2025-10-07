import os
import unittest
import pytest

# Import the workflow controller
from services.backend.src.workflow_controller import call_workflow

@pytest.mark.integration
class TestWorkflowControllerOllamaIntegration(unittest.TestCase):
    """
    Integration tests for calling Ollama model through the workflow controller's default workflow.
    These tests require an actual Ollama service to be running.
    """

    def setUp(self):
        """
        Set up the test environment.
        """
        # Check if Ollama service is available
        self.ollama_service_url = os.getenv("OLLAMA_SERVICE_URL")
        if not self.ollama_service_url:
            self.skipTest("OLLAMA_SERVICE_URL environment variable is not set. Skipping integration tests.")

    def test_call_workflow_with_ollama_integration(self, ollama_config):
        """
        Integration test for calling the default workflow with Ollama model.
        """

        # Call the workflow controller with Ollama config
        result = call_workflow("What is machine learning?", config=ollama_config)

        # Assertions
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_call_workflow_with_ollama_different_model_integration(self, ollama_config_mistral):
        """
        Integration test for calling the default workflow with a different Ollama model.
        """

        # Call the workflow controller with Ollama config for mistral model
        result = call_workflow("Explain quantum computing", config=ollama_config_mistral)

        # Assertions
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

if __name__ == '__main__':
    unittest.main()
