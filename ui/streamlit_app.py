"""
Streamlit chat interface for the RAG API.

Run the FastAPI backend first (in a separate terminal):
    uvicorn src.app:app --reload

Then run this UI (in another terminal):
    streamlit run ui/streamlit_app.py
"""

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/query"

st.set_page_config(page_title="Enterprise RAG Assistant", page_icon="🤖")
st.title("🤖 Enterprise RAG Assistant")
st.caption("Ask a question about the ingested documents.")

# Keep chat history across reruns (Streamlit reruns the whole script on every interaction)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            st.caption(f"Sources: {', '.join(message['sources'])}")

# Chat input
question = st.chat_input("Ask a question...")

if question:
    # Show the user's message immediately
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Call the API and show the assistant's response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(API_URL, json={"question": question}, timeout=60)
                response.raise_for_status()
                data = response.json()

                answer = data["answer"]
                sources = data.get("sources", [])
                blocked = data.get("blocked", False)

                st.markdown(answer)
                if sources and not blocked:
                    st.caption(f"Sources: {', '.join(sources)}")

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )
            except requests.exceptions.ConnectionError:
                error_msg = "Can't reach the API. Is `uvicorn src.app:app --reload` running?"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})