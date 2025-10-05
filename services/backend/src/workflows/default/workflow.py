import os

from .config import create_config

from .model_builder import create_llm
from .prompt_builder import build_langfuse_prompt, get_messages


def default_workflow(data, **kwargs):
    if 'config' in kwargs:
        config = kwargs['config']
    else:
        config = create_config("google")

    llm = create_llm(config)

    if 'prompt_name' in kwargs:
        prompt_name = kwargs['prompt']
    else:
        prompt_name = "default"
    if 'tag' in kwargs:
        tag = kwargs['tag']
    else:
        tag = "production"

    prompt = build_langfuse_prompt(prompt_name, llm, tag)

    messages = get_messages(data, **kwargs)

    re = llm.invoke(messages)
    return re