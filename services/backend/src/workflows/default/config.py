def create_config(provider, temperature=0, max_retries=3) -> dict:
    return {
        "provider": provider,
        "temperature": temperature,
        "max_retries": max_retries
    }