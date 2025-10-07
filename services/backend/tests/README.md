# Backend Service Tests

This directory contains the automated tests for the backend service. The tests are written using `pytest` and are divided into unit and integration tests.

## Test Structure

  * **`test_workflow_controller_ollama.py`**: Contains unit tests for the workflow controller. These tests use mocks to isolate the controller and verify its behavior without external dependencies.
  * **`test_workflow_controller_ollama_integration.py`**: Contains integration tests that verify the workflow controller's interaction with a running Ollama service.
  * **`conftest.py`**: A `pytest` configuration file that defines fixtures and custom markers used across the test suite.

## Running the Tests

Follow these instructions to run the tests.

### Prerequisites

  * Python 3.12 or higher
  * `pytest`
  * `unittest.mock`

### Running Unit Tests

To run the unit tests, which do not require any external services, execute the following command from the project's root directory:

```bash
python -m pytest services/backend/tests/test_workflow_controller_ollama.py -v
```

### Running Integration Tests

The integration tests require a running Ollama service. Before running these tests, ensure that the `OLLAMA_SERVICE_URL` environment variable is set.

1.  **Set the environment variable:**

    ```bash
    export OLLAMA_SERVICE_URL=http://localhost:11434  # Adjust if your Ollama service runs on a different URL
    ```

2.  **Run the integration tests:**

    ```bash
    python -m pytest services/backend/tests/test_workflow_controller_ollama_integration.py -v
    ```

    Alternatively, you can run all tests marked as `integration`:

    ```bash
    python -m pytest services/backend/tests -m integration -v
    ```

### Running All Tests

To run both unit and integration tests, use the following command:

```bash
python -m pytest services/backend/tests -v
```

## Test Coverage

The tests cover a variety of scenarios, including:

  * **Unit Tests**:
      * Calling the default workflow with a mocked Ollama model (`llama2`).
      * Calling the default workflow with a different mocked Ollama model (`mistral`).
  * **Integration Tests**:
      * Verifying the end-to-end functionality of the workflow controller with a live Ollama service.

## Pytest Fixtures

The tests make use of fixtures defined in `conftest.py` to provide consistent and reusable test data:

  * **`ollama_config`**: A fixture that provides a configuration dictionary for the `llama2` model.
  * **`ollama_config_mistral`**: A fixture that provides a configuration for the `mistral` model.

These fixtures simplify the test setup and make it easy to test with different model configurations.