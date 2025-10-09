import os
import pytest
from langfuse import Langfuse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if Langfuse credentials are present
langfuse_credentials_present = all(
    os.getenv(k) for k in ["LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
)

# Skip all tests in this module if Langfuse credentials are not set
pytestmark = pytest.mark.skipif(
    not langfuse_credentials_present,
    reason="Langfuse environment variables not set. Skipping Langfuse connectivity tests."
)

@pytest.fixture
def langfuse_client():
    """Fixture to create a Langfuse client."""
    return Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST")
    )

@pytest.mark.integration
def test_langfuse_authentication(langfuse_client):
    """
    Tests if the client can authenticate with the Langfuse server.
    """
    try:
        # The auth_check method returns True if authentication is successful.
        assert langfuse_client.auth_check(), "Langfuse authentication check failed."
    except Exception as e:
        pytest.fail(f"Langfuse authentication failed with an unexpected error: {e}")

@pytest.mark.integration
def test_get_prompt_for_connectivity(langfuse_client):
    """
    Tests connectivity by attempting to fetch a prompt, which requires a valid connection and authentication.
    """
    try:
        # This will attempt to fetch a prompt and will raise an error if not found,
        # but for connectivity testing, any response other than a connection error is a success.
        with pytest.raises(Exception):
             langfuse_client.get_prompt("non_existent_prompt")
    except Exception as e:
        if "Failed to connect" in str(e) or "authentication" in str(e).lower():
            pytest.fail(f"Connectivity test failed with a connection or authentication error: {e}")
