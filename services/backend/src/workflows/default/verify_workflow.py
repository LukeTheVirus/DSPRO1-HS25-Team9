import langfuse

from services.backend.src.workflows.helpers.config import create_config
from services.backend.src.workflows.helpers.model_builder import create_llm
from services.backend.src.workflows.helpers.prompt_builder import build_langfuse_prompt, get_messages


def verify_workflow(user_input, **kwargs):
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
