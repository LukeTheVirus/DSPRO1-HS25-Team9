from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from pydantic import SecretStr
import os

def create_llm(config, max_tokens=None, timeout=None):
    """
    Factory function to create a Langchain Chat LLM based on the provided configuration.

    Args:
        config (dict): A dictionary containing the provider, model, temperature, and max_retries.
        max_tokens (int, optional): The maximum number of tokens to generate.
        timeout (int, optional): The timeout for the API call.

    Returns:
        A Langchain chat model instance.
    """
    provider = config.get("provider")
    api_key = None

    if provider == "google":
        api_key = os.getenv("GOOGLE_API_KEY")
        return ChatGoogleGenerativeAI(
            model=config["model"],
            temperature=config["temperature"],
            max_output_tokens=max_tokens,
            timeout=timeout,
            max_retries=config["max_retries"],
            google_api_key=api_key
        )
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        return ChatOpenAI(
            model=config["model"],
            temperature=config["temperature"],
            timeout=timeout,
            max_retries=config["max_retries"],
            api_key=SecretStr(api_key) if api_key else None
        )
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        return ChatDeepSeek(
            model=config["model"],
            temperature=config["temperature"],
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=config["max_retries"],
            api_key=SecretStr(api_key) if api_key else None
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")