import os
import json
import time
import requests
import streamlit as st

OLLAMA_URL = os.getenv("BACKEND_URL", "http://localhost:11434")  # <- Ollama
MODEL = os.getenv("MODEL", "mistral:latest")
HEADERS_JSON = {"Content-Type": "application/json"}

st.set_page_config(page_title="Chatbot", page_icon="💬", layout="centered")
st.title("Chatbot (Ollama)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render History
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Type your message…")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        partial = ""

        try:
            # ---- Option 1: Non-Streaming (einfach) ----
            # Stream ausschalten, dann kommt eine einzige JSON-Antwort.
            resp = requests.post(
                f"{OLLAMA_URL}/api/chat",
                headers=HEADERS_JSON,
                data=json.dumps({
                    "model": MODEL,
                    "messages": st.session_state.messages,
                    "stream": False
                }),
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json()
            partial = data["message"]["content"]
            placeholder.markdown(partial)

            # ---- Option 2: Streaming (wenn gewünscht) ----
            # # resp = requests.post(
            # #     f"{OLLAMA_URL}/api/chat",
            # #     headers=HEADERS_JSON,
            # #     data=json.dumps({"model": MODEL, "messages": st.session_state.messages, "stream": True}),
            # #     stream=True, timeout=300
            # # )
            # # for line in resp.iter_lines(decode_unicode=True):
            # #     if not line: 
            # #         continue
            # #     chunk = json.loads(line)
            # #     delta = chunk.get("message", {}).get("content", "")
            # #     partial += delta
            # #     placeholder.markdown(partial)

        except Exception as e:
            partial = f"⚠️ Error contacting Ollama: {e}"
            placeholder.markdown(partial)

    st.session_state.messages.append({"role": "assistant", "content": partial})

