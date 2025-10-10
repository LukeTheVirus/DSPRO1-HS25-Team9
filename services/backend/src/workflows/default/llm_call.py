import logging
import os

from langfuse._client.get_client import get_client
from langfuse._client.observe import observe

from .prompt_builder import get_messages

@observe(name="example_call")
def make_call_example(llm, **kwargs):
    messages = get_messages(**kwargs)
    return llm.invoke(messages)

if __name__ == '__main__':
    if not all(os.getenv(k) for k in ["LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]):
        try:
            import config
            langfuse = get_client()
        except Exception as e:
            logging.error(f"Error loading environment variables: {e}")
            logging.error("Missing required Langfuse environment variables. Tracing will be disabled.")
    else:
        langfuse = get_client()
        logging.info("Langfuse environment variables found. Tracing enabled.")

