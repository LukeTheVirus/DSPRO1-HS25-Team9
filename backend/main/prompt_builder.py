from langchain_core.prompts import ChatPromptTemplate


def build_langfuse_prompt(prompt_name, langfuse, target_tag):
    langf_host = langfuse.get_client()

    try:
        langfuse_prompt = langf_host.get_prompt(
            name=prompt_name,
            label="production" if not target_tag else target_tag
        )
    except Exception as e:
        print(f"Could not fetch prompt '{prompt_name}' with tag '{target_tag}'. Falling back to latest. Error: {e}")

    messages = langfuse_prompt.prompt

    # The langchain_prompt_template is now compiled from the messages
    langchain_prompt_template = ChatPromptTemplate.from_messages(messages)

    return langchain_prompt_template

def get_messages(langchain_prompt_template, **kwargs):
    """
    Formats the prompt template with the given inputs.
    """
    formatted_messages = langchain_prompt_template.format_messages(**kwargs)
    return formatted_messages