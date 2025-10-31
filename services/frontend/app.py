import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import streamlit as st

# --- Config ---
DEFAULT_BACKEND = os.getenv("BACKEND_URL", "http://backend:8000")
DEFAULT_WORKFLOW = "default"
TITLE = os.getenv("APP_TITLE", "Chatbot")
HEADERS_JSON = {"Content-Type": "application/json"}
REQUEST_TIMEOUT = 120


def _ensure_session_state():
    if "conversation" not in st.session_state:
        st.session_state.conversation = []  # [{"user": str, "assistant": Dict[str, Any]}]
    st.session_state.setdefault("watcher_status", None)
    st.session_state.setdefault("health_status", None)
    st.session_state.setdefault("watch_directory", "/app/uploads")
    st.session_state.setdefault("watcher_feedback", None)


def _inject_dark_theme():
    st.markdown(
        """
        <style>
            :root {
                color-scheme: dark;
            }
            .stApp {
                background: linear-gradient(160deg, #0b0f19 0%, #131b2e 60%, #06070b 100%);
                color: #f5f7fa;
            }
            .stMarkdown, .stText, .stSubheader, .stCaption, .stTitle {
                color: #dbe2ff !important;
            }
            .stMarkdown a { color: #7fb3ff; }
            .stChatMessageContainer {
                border-radius: 12px;
                background-color: rgba(255, 255, 255, 0.04);
                padding: 8px 16px;
            }
            .main .block-container {
                max-width: 90vw !important;
                padding-top: 2.5rem;
                padding-bottom: 3.5rem;
            }
            div[data-testid="stMainBlockContainer"] > div {
                max-width: 90vw !important;
            }
            div[data-testid="stChatMessageList"] {
                max-width: 80vw;
                margin: 0 auto 2rem auto;
            }
            div[data-testid="stChatMessage"] {
                display: flex;
                width: 100%;
            }
            div[data-testid="stChatMessage"] .stChatMessageContainer {
                max-width: 70%;
                box-shadow: 0 12px 24px rgba(8, 12, 24, 0.35);
                border: 1px solid rgba(255, 255, 255, 0.06);
            }
            div[data-testid="stChatMessage-user"] .stChatMessageContainer {
                margin-left: auto;
                background: linear-gradient(135deg, rgba(55, 86, 255, 0.85), rgba(109, 136, 255, 0.8));
                color: #f9fbff !important;
                text-align: right;
            }
            div[data-testid="stChatMessage-assistant"] .stChatMessageContainer {
                margin-right: auto;
                background: rgba(16, 23, 40, 0.85);
            }
            div[data-testid="stChatMessage-user"] .stCaption,
            div[data-testid="stChatMessage-user"] p,
            div[data-testid="stChatMessage-user"] span {
                color: #f9fbff !important;
            }
            div[data-testid="stChatMessage-assistant"] .stCaption {
                color: rgba(214, 223, 255, 0.7) !important;
            }
            div[data-testid="stChatMessage-user"] div[data-testid="stMarkdownContainer"],
            div[data-testid="stChatMessage-user"] div[data-testid="stMarkdown"] {
                text-align: right !important;
            }
            div[data-testid="stChatMessageContent"] > div[data-testid="stVerticalBlockBorderWrapper"] {
                width: 100% !important;
            }
            div[data-testid="stChatMessageContent"] div[data-testid="stVerticalBlock"],
            div[data-testid="stChatMessageContent"] div[data-testid="stElementContainer"],
            div[data-testid="stChatMessageContent"] div[data-testid="stMarkdown"] {
                width: 100% !important;
            }
            div[data-testid="stChatInputContainer"] div[data-baseweb="base-input"],
            div[data-testid="stChatInputContainer"] textarea {
                max-width: 80vw;
                margin: 0 auto;
            }
            section[data-testid="stSidebar"],
            div[data-testid="stSidebar"] {
                background: linear-gradient(185deg, #050812 0%, #0c1322 40%, #111c32 100%) !important;
                color: #e4e9ff !important;
                border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
            }
            section[data-testid="stSidebar"] > div,
            div[data-testid="stSidebar"] > div {
                padding: 1.6rem 1.4rem !important;
            }
            div[data-testid="stSidebarHeader"],
            div[data-testid="stSidebarUserContent"],
            div[data-testid="stSidebarContent"] {
                background: transparent !important;
            }
            div[data-testid="stSidebarContent"] * {
                color: #dde4ff !important;
            }
            div[data-testid="stSidebarContent"] h1,
            div[data-testid="stSidebarContent"] h2,
            div[data-testid="stSidebarContent"] h3 {
                color: #f2f4ff !important;
            }
            div[data-testid="stSidebarContent"] .stTabs [data-baseweb="tab-list"] {
                display: flex !important;
                gap: 8px !important;
            }
            div[data-testid="stSidebarContent"] .stTabs [data-baseweb="tab"] {
                flex: 1 1 0 !important;
                margin: 0 !important;
                color: rgba(205, 215, 255, 0.68) !important;
                background: rgba(22, 30, 54, 0.45) !important;
                border-radius: 10px !important;
                padding: 0.4rem 0.9rem !important;
                justify-content: center !important;
            }
            div[data-testid="stSidebarContent"] .stTabs [aria-selected="true"] {
                background: rgba(63, 83, 140, 0.85) !important;
                color: #ffffff !important;
                box-shadow: 0 6px 18px rgba(54, 74, 135, 0.35);
            }
            div[data-testid="stSidebarContent"] hr {
                border-color: rgba(86, 108, 180, 0.35) !important;
            }
            div[data-testid="stSidebarContent"] label,
            div[data-testid="stSidebarContent"] .stCaption,
            div[data-testid="stSidebarContent"] p {
                color: rgba(215, 223, 255, 0.7) !important;
            }
            div[data-testid="stSidebarContent"] .stButton>button {
                box-shadow: 0 8px 18px rgba(21, 58, 254, 0.25);
            }
            div[data-testid="stSidebarContent"] .stExpander,
            div[data-testid="stSidebarContent"] details {
                background: rgba(20, 26, 44, 0.6) !important;
                border: 1px solid rgba(83, 99, 150, 0.4) !important;
                border-radius: 10px !important;
            }
            .st-emotion-cache-128upt6 {
                background: rgba(15, 19, 32, 0.9) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
            }
            .stButton>button {
                background: #275bff;
                color: #ffffff;
                border: 0;
                border-radius: 8px;
                transition: background 0.2s ease, transform 0.2s ease;
            }
            .stButton>button:hover {
                background: #3c6dff;
                transform: translateY(-1px);
            }
            header[data-testid="stHeader"] {
                background: rgba(7, 11, 20, 0.92) !important;
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
            header[data-testid="stHeader"] * {
                color: #dbe3ff !important;
            }
            header[data-testid="stHeader"] button {
                background-color: rgba(18, 26, 43, 0.8) !important;
                border-radius: 6px !important;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 6px;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: rgba(255, 255, 255, 0.05);
                color: #dce2f5;
                border-radius: 6px 6px 0 0;
            }
            .stTabs [aria-selected="true"] {
                background: rgba(255, 255, 255, 0.12) !important;
                color: #fff !important;
            }
            code, pre {
                background-color: rgba(12, 15, 25, 0.95) !important;
                color: #f1f5ff !important;
            }
            .stCode, .st-emotion-cache-12r09dv {
                background: rgba(12, 15, 25, 0.95) !important;
                color: #f1f5ff !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                border-radius: 8px !important;
            }
            textarea, input, .stChatInputContainer {
                background-color: rgba(15, 19, 32, 0.85) !important;
                color: #f5f7fa !important;
                border: 1px solid rgba(255, 255, 255, 0.12) !important;
            }
            textarea::placeholder, input::placeholder {
                color: rgba(220, 228, 255, 0.5) !important;
            }
            .stTextInput>div>div>input {
                color: #f5f7fa !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _reset_chat():
    st.session_state.conversation = []


def call_generation_api(query: str, backend_url: str, workflow_name: str) -> Dict[str, Any]:
    endpoint = backend_url.rstrip("/") + "/generate"
    payload: Dict[str, Any] = {"query": query}
    if workflow_name and workflow_name != DEFAULT_WORKFLOW:
        payload["workflow_name"] = workflow_name

    response = requests.post(endpoint, json=payload, headers=HEADERS_JSON, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    return {
        "final_answer": data.get("final_answer") or data.get("response") or "",
        "generated_search_query": data.get("generated_search_query"),
        "retrieved_context": data.get("retrieved_context", {}),
        "raw": data,
    }


def fetch_watcher_status(backend_url: str) -> Dict[str, Any]:
    endpoint = backend_url.rstrip("/") + "/watch/status"
    response = requests.get(endpoint, timeout=30)
    response.raise_for_status()
    return response.json()


def start_watching_directory(backend_url: str, directory: str) -> Dict[str, Any]:
    endpoint = backend_url.rstrip("/") + "/watch/start"
    response = requests.post(endpoint, params={"directory": directory}, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_health_status(backend_url: str) -> Dict[str, Any]:
    endpoint = backend_url.rstrip("/") + "/health"
    response = requests.get(endpoint, timeout=30)
    response.raise_for_status()
    return response.json()


def _render_context(context: Dict[str, Any]):
    if not context:
        return

    st.markdown("**Retrieved context**")
    for doc_id, payload in context.items():
        title = Path(doc_id).name or doc_id
        meta_parts = []
        if isinstance(payload, dict):
            best_score = payload.get("best_score")
            if isinstance(best_score, (int, float)):
                meta_parts.append(f"best score: {best_score:.3f}")
            chunks = payload.get("retrieved_chunks")
            if isinstance(chunks, int):
                meta_parts.append(f"chunks: {chunks}")
            header = f"{title}"
            if meta_parts:
                header += f" ({' • '.join(meta_parts)})"
            with st.expander(header, expanded=False):
                st.markdown(payload.get("text_content", ""))
        else:
            with st.expander(title, expanded=False):
                st.markdown(str(payload))


def render_assistant_reply(reply: Dict[str, Any]):
    final_answer = reply.get("final_answer") or "ℹ️ Backend returned an empty response."
    st.markdown(final_answer)

    generated_search_query = reply.get("generated_search_query")
    if generated_search_query:
        st.markdown("**Answer without context**")
        st.markdown(generated_search_query)

    _render_context(reply.get("retrieved_context") or {})


def render_watcher_status(status: Optional[Dict[str, Any]]):
    if not status:
        st.info("Watcher status unavailable. Refresh to try again.")
        return

    watchers = status.get("watchers", [])
    if not watchers:
        st.markdown("No active watchers.")
        return

    st.markdown("**Active watchers**")
    for watcher in watchers:
        directory = watcher.get("directory", "Unknown directory")
        stats = (
            f"Tracked files: {watcher.get('tracked_files', 0)} • "
            f"Processing: {watcher.get('currently_processing', 0)} • "
            f"Ingesting: {watcher.get('files_being_ingested', 0)}"
        )
        with st.expander(directory, expanded=False):
            st.markdown(stats)


def render_health_status(health: Optional[Dict[str, Any]]):
    if not health:
        st.info("Health status unavailable. Refresh to try again.")
        return

    overall = health.get("status", "unknown").title()
    st.markdown(f"**Overall status:** {overall}")

    services = health.get("services", {})
    if not services:
        return

    for name, info in services.items():
        label = name.title()
        status = info.get("status", "unknown")
        detail = info.get("error")
        status_label = status.title()
        text = f"{status_label}"
        if detail:
            text += f" — {detail}"
        st.markdown(f"- **{label}:** {text}")


def main():
    st.set_page_config(page_title=TITLE, page_icon="💬", layout="centered")
    _ensure_session_state()
    _inject_dark_theme()

    with st.sidebar:
        st.header("Control Center")
        tabs = st.tabs(["Chat", "Watcher", "Health"])

        with tabs[0]:
            backend_input = st.text_input(
                "Backend URL",
                st.session_state.get("backend_url", DEFAULT_BACKEND),
            )
            backend_url = backend_input.strip() or DEFAULT_BACKEND
            st.session_state["backend_url"] = backend_url

            workflow_input = st.text_input(
                "Workflow name",
                st.session_state.get("workflow_name", DEFAULT_WORKFLOW),
            )
            workflow_name = workflow_input.strip() or DEFAULT_WORKFLOW
            st.session_state["workflow_name"] = workflow_name

            st.button("Clear chat history", on_click=_reset_chat, use_container_width=True)
            st.caption("Messages are sent to /generate")

        with tabs[1]:
            backend_url = st.session_state.get("backend_url", DEFAULT_BACKEND)
            st.session_state["watch_directory"] = st.text_input(
                "Directory to watch",
                st.session_state.get("watch_directory", "/app/uploads"),
            ).strip() or st.session_state.get("watch_directory", "/app/uploads")

            start_col, refresh_col = st.columns(2)

            with start_col:
                if st.button("Start watcher", use_container_width=True):
                    directory = st.session_state["watch_directory"]
                    try:
                        response = start_watching_directory(backend_url, directory)
                        st.session_state["watcher_feedback"] = {
                            "type": "success",
                            "message": response.get("status", "Watcher command sent."),
                        }
                        st.session_state["watcher_status"] = fetch_watcher_status(backend_url)
                    except requests.RequestException as exc:
                        st.session_state["watcher_feedback"] = {
                            "type": "error",
                            "message": f"Failed to start watcher: {exc}",
                        }

            with refresh_col:
                if st.button("Refresh status", use_container_width=True):
                    try:
                        st.session_state["watcher_status"] = fetch_watcher_status(backend_url)
                        st.session_state.setdefault("watcher_feedback", None)
                    except requests.RequestException as exc:
                        st.session_state["watcher_feedback"] = {
                            "type": "error",
                            "message": f"Failed to fetch status: {exc}",
                        }

            feedback = st.session_state.get("watcher_feedback")
            if feedback:
                if feedback["type"] == "success":
                    st.success(feedback["message"])
                else:
                    st.error(feedback["message"])

            if st.session_state.get("watcher_status") is None:
                try:
                    st.session_state["watcher_status"] = fetch_watcher_status(backend_url)
                except requests.RequestException:
                    st.session_state["watcher_status"] = None

            render_watcher_status(st.session_state.get("watcher_status"))

        with tabs[2]:
            backend_url = st.session_state.get("backend_url", DEFAULT_BACKEND)
            if st.button("Refresh health", use_container_width=True):
                try:
                    st.session_state["health_status"] = fetch_health_status(backend_url)
                except requests.RequestException as exc:
                    st.session_state["health_status"] = {
                        "status": "error",
                        "services": {},
                        "error": str(exc),
                    }

            if st.session_state.get("health_status") is None:
                try:
                    st.session_state["health_status"] = fetch_health_status(backend_url)
                except requests.RequestException:
                    st.session_state["health_status"] = None

            render_health_status(st.session_state.get("health_status"))

    # Render previous conversation
    for exchange in st.session_state.conversation:
        with st.chat_message("user"):
            st.markdown(exchange["user"])
        assistant_reply = exchange.get("assistant")
        if assistant_reply:
            with st.chat_message("assistant"):
                render_assistant_reply(assistant_reply)

    prompt = st.chat_input("Ask a question…")
    if prompt:
        backend_url = st.session_state.get("backend_url", DEFAULT_BACKEND)
        workflow_name = st.session_state.get("workflow_name", DEFAULT_WORKFLOW)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                with st.spinner("Generating answer…"):
                    reply = call_generation_api(prompt, backend_url, workflow_name)
                render_assistant_reply(reply)
            except requests.HTTPError as http_err:
                detail = http_err.response.text if http_err.response is not None else str(http_err)
                reply = {"final_answer": f"⚠️ Backend error: {detail}"}
                st.markdown(reply["final_answer"])
            except Exception as exc:
                reply = {"final_answer": f"⚠️ Error contacting backend: {exc}"}
                st.markdown(reply["final_answer"])

        st.session_state.conversation.append({"user": prompt, "assistant": reply})


if __name__ == "__main__":
    main()
