import os

import langfuse

from .config import create_config

from .model_builder import create_llm
from .prompt_builder import build_langfuse_prompt, get_messages


def langfuse_test(user_input, **kwargs):
    if 'config' in kwargs:
        config = kwargs['config']
    else:
        config = create_config("ollama")

    llm = create_llm(config)

    lf_client = langfuse.get_client()
    prompt = build_langfuse_prompt("test", lf_client, "production")

    messages = get_messages(prompt, input=user_input, **kwargs)

    re = llm.invoke(messages)
    return re.content