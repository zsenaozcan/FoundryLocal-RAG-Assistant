"""
Browser-based UI for the offline movie RAG assistant, using Streamlit.

Supports multiple independent chat sessions within this browser tab,
switchable from the sidebar. Note: each question is still answered
independently via RAG - answer_query() does not use earlier messages in
the same chat as context, so this only organizes your Q&A history
visually, it doesn't add conversational memory.

Streamlit runs its own local web server (default: http://localhost:8501).
No internet connection is required for the assistant itself.

Run with: streamlit run streamlit_app.py
"""

import time

import streamlit as st

from assistant import answer_query

st.set_page_config(page_title="Local Movie RAG Assistant", page_icon="🎬", layout="wide")

USER_AVATAR = "🙋"
ASSISTANT_AVATAR = "🎬"

st.markdown(
    """
    <style>
    .movie-banner {
        background: linear-gradient(135deg, #1B1E3D 0%, #3A1C5A 50%, #10121C 100%);
        padding: 2rem 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }
    .movie-banner h1 {
        margin: 0;
        font-size: 2.2rem;
    }
    .movie-banner p {
        margin-top: 0.5rem;
        opacity: 0.85;
    }
    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 0.5rem 0.25rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }
    [data-testid="stChatInput"] {
        border-radius: 20px;
    }
    [data-testid="stSidebar"] button {
        border-radius: 10px !important;
        transition: transform 0.15s ease;
    }
    [data-testid="stSidebar"] button:hover {
        transform: scale(1.02);
    }
    div[data-testid="stStatusWidget"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def new_chat():
    chat_id = str(time.time())
    st.session_state.chats[chat_id] = {"name": "New Chat", "messages": []}
    st.session_state.active_chat_id = chat_id


if "chats" not in st.session_state:
    st.session_state.chats = {}
    st.session_state.active_chat_id = None
    new_chat()

with st.sidebar:
    st.title("🎬 Chats")
    if st.button("+ New Chat", use_container_width=True):
        new_chat()

    st.divider()

    for chat_id, chat in list(st.session_state.chats.items()):
        is_active = chat_id == st.session_state.active_chat_id
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(
                chat["name"],
                key=f"select_{chat_id}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.active_chat_id = chat_id
                st.rerun()
        with col2:
            if len(st.session_state.chats) > 1:
                if st.button("🗑", key=f"delete_{chat_id}"):
                    del st.session_state.chats[chat_id]
                    if st.session_state.active_chat_id == chat_id:
                        st.session_state.active_chat_id = next(iter(st.session_state.chats))
                    st.rerun()

active_chat = st.session_state.chats[st.session_state.active_chat_id]

st.markdown(
    """
    <div class="movie-banner">
        <h1>🎬 Local Movie RAG Assistant</h1>
        <p>Ask about a movie's plot, cast, or director — or ask for a recommendation by year and/or genre. Runs fully offline, no internet required.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

for message in active_chat["messages"]:
    avatar = USER_AVATAR if message["role"] == "user" else ASSISTANT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.write(message["content"])

question = st.chat_input("Ask a question about a movie...")

if question:
    active_chat["messages"].append({"role": "user", "content": question})
    if active_chat["name"] == "New Chat":
        active_chat["name"] = question[:30] + ("..." if len(question) > 30 else "")

    with st.spinner("Thinking..."):
        answer = answer_query(question, show_retrieved=False)

    active_chat["messages"].append({"role": "assistant", "content": answer})
    st.rerun()