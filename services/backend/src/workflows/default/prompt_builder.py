from langchain_core.prompts import ChatPromptTemplate


from langchain_core.prompts import ChatPromptTemplate


def build_langfuse_prompt(prompt_name, langfuse_client, target_tag):
    try:
        langfuse_prompt = langfuse_client.get_prompt(
            name=prompt_name,
            label="production" if not target_tag else target_tag
        )
    except Exception as e:
        print(f"Could not fetch prompt '{prompt_name}' with tag '{target_tag}'. Falling back to latest. Error: {e}")
        # As a fallback, create a simple template. In a real application, you might handle this differently.
        return ChatPromptTemplate.from_template("{input}")


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