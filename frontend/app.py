import os
import json
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
    backend_url = st.text_input("Backend URL", DEFAULT_BACKEND, key="backend_url")
    st.caption("Your FastAPI backend with /chat and /rag/query")
    if st.button("Clear chat"):
        st.session_state.pop("messages", None)
        st.rerun()
    st.divider()
    st.caption("v0.1")

st.title(TITLE)

# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []  # [{"role":"user"|"assistant","content":"..."}]

# --- Render history ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
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
            # Call YOUR backend (non-streaming)
            resp = requests.post(
                f"{st.session_state.backend_url}/chat",
                headers=HEADERS_JSON,
                data=json.dumps({
                    "messages": st.session_state.messages,
                    "stream": False,          # backend can ignore/extend later
                }),
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json()

            # Your backend returns {"answer": "..."}
            # Fallback to Ollama-style if ever pointed directly at Ollama.
            answer = data.get("answer") or data.get("message", {}).get("content", "")

            # (optional) fake streaming for nicer UX
            for token in answer.split():
                partial += token + " "
                placeholder.markdown(partial)
                time.sleep(0.01)

        except Exception as e:
            partial = f"⚠️ Error contacting backend: {e}"
            placeholder.markdown(partial)

    # persist assistant message
    st.session_state.messages.append({"role": "assistant", "content": partial})

