import os
import json
import time
import requests
import streamlit as st
import streamlit.components.v1 as components

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
    
# --- Helper: copy to clipboard (runs in browser) ---
def copy_to_clipboard(text: str):
    # Use a tiny HTML/JS bridge; height 0 keeps it invisible
    components.html(
        f"""
        <script>
        const text = {json.dumps(text)};
        navigator.clipboard.writeText(text)
          .then(() => {{
            window.parent.postMessage({{ stCopyDone: true }}, "*");
          }})
          .catch(() => {{
            // Fallback: create a temp textarea
            const ta = document.createElement('textarea');
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            window.parent.postMessage({{ stCopyDone: true }}, "*");
          }});
        </script>
        """,
        height=0,
    )
    # Show a toast immediately on the Python side too
    st.toast("Copied to clipboard")

# --- Render history with Copy buttons ---
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        # Top bar with role label and copy button
        left, right = st.columns([0.8, 0.2])
        with left:
            st.caption(m["role"].title())
        with right:
            if st.button("📋 Copy", key=f"copy_{i}"):
                copy_to_clipboard(m["content"])
        # Message content
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

            # Your backend returns {"answer": "..."};
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
