import os
import time
import requests
import streamlit as st

# --- Config ---
DEFAULT_BACKEND = os.getenv("BACKEND_URL", "http://backend:8000")  # compose service
TITLE = os.getenv("APP_TITLE", "Chatbot")
HEADERS_JSON = {"Content-Type": "application/json"}

st.set_page_config(page_title=TITLE, page_icon="💬", layout="centered")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    backend_saved = st.session_state.get("backend_url", DEFAULT_BACKEND)
    backend_url = st.text_input("Backend URL", backend_saved).strip() or DEFAULT_BACKEND
    st.session_state["backend_url"] = backend_url

    workflow_saved = st.session_state.get("workflow_name", "default")
    workflow_name = st.text_input("Workflow name", workflow_saved).strip() or "default"
    st.session_state["workflow_name"] = workflow_name

    st.subheader("LLM configuration")
    override_config = st.checkbox(
        "Override backend defaults",
        value=st.session_state.get("override_config", False)
    )
    st.session_state["override_config"] = override_config

    config = None
    if override_config:
        provider_options = ["ollama", "openai", "google", "deepseek"]
        provider_saved = st.session_state.get("provider", provider_options[0])
        provider_index = provider_options.index(provider_saved) if provider_saved in provider_options else 0
        provider = st.selectbox("Provider", provider_options, index=provider_index)
        st.session_state["provider"] = provider

        default_model = "phi4-mini" if provider == "ollama" else st.session_state.get("model", "gpt-4o-mini")
        model_name = st.text_input("Model ID", default_model).strip()
        if not model_name:
            model_name = default_model
        st.session_state["model"] = model_name

        temperature_saved = st.session_state.get("temperature", 0.2)
        temperature = st.slider("Temperature", 0.0, 1.0, float(temperature_saved), 0.05)
        st.session_state["temperature"] = temperature

        retries_saved = st.session_state.get("max_retries", 3)
        max_retries = st.number_input("Max retries", min_value=0, max_value=10, value=int(retries_saved), step=1)
        st.session_state["max_retries"] = max_retries

        config = {
            "provider": provider,
            "model": model_name,
            "temperature": float(temperature),
            "max_retries": int(max_retries)
        }

        if provider == "ollama":
            base_url_saved = st.session_state.get("ollama_base_url", "http://ollama:11434")
            base_url = st.text_input("Ollama base URL", base_url_saved).strip()
            if not base_url:
                base_url = base_url_saved
            st.session_state["ollama_base_url"] = base_url
            config["base_url"] = base_url

    st.caption("Targets FastAPI backend /generate endpoint")
    if st.button("Clear chat"):
        st.session_state.pop("messages", None)
        st.rerun()
    st.divider()
    st.caption("v0.1")

st.title(TITLE)

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []  # [{"role":"user"|"assistant","content":"..."}]


def call_generation_api(query: str, backend_url: str, workflow_name: str, config_override: dict | None) -> str:
    endpoint = backend_url.rstrip("/") + "/generate"
    payload = {"query": query, "workflow_name": workflow_name}
    if config_override:
        payload["config"] = config_override

    response = requests.post(endpoint, json=payload, headers=HEADERS_JSON, timeout=300)
    response.raise_for_status()
    data = response.json()
    return data.get("response") or data.get("message", {}).get("content", "")
    
# --- Render history ---
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.caption(m["role"].title())
        st.markdown(m["content"])
        
# --- Input ---
prompt = st.chat_input("Type your message…")
if prompt:
    # append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # assistant placeholder
    with st.chat_message("assistant"):
        placeholder = st.empty()
        partial = ""

        try:
            answer = call_generation_api(prompt, backend_url, workflow_name, config)

            # (optional) fake streaming for nicer UX
            for token in answer.split():
                partial += token + " "
                placeholder.markdown(partial)
                time.sleep(0.01)

            if answer:
                partial = answer
                placeholder.markdown(partial)
            else:
                partial = "ℹ️ Backend returned an empty response."
                placeholder.markdown(partial)

        except requests.HTTPError as http_err:
            detail = http_err.response.text if http_err.response is not None else str(http_err)
            partial = f"⚠️ Backend error: {detail}"
            placeholder.markdown(partial)
        except Exception as e:
            partial = f"⚠️ Error contacting backend: {e}"
            placeholder.markdown(partial)

    # persist assistant message
    st.session_state.messages.append({"role": "assistant", "content": partial})
