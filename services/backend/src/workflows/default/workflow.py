import os

from .config import create_config

from .model_builder import create_llm
from .prompt_builder import build_langfuse_prompt, get_messages


def default_workflow(user_input, **kwargs):
    if 'config' in kwargs:
        config = kwargs['config']
    else:
        config = create_config("google")

    llm = create_llm(config)

    from langchain_core.prompts import ChatPromptTemplate
    prompt = ChatPromptTemplate.from_template("{input}")

    messages = get_messages(prompt, input=user_input, **kwargs)

    re = llm.invoke(messages)
    return re