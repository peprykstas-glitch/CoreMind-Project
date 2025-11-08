import streamlit as st
import requests
import time
import os
from dotenv import load_dotenv

# --- 0. Page Config & CSS Styles ---
st.set_page_config(
    page_title="CoreMind v0.6",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Block (Your existing dark theme CSS) ---
st.markdown("""
<style>
    /* ... (Весь ваш довгий CSS-блок з темною темою v2.1) ... */
</style>
""", unsafe_allow_html=True)
# --- End of CSS Block ---


# --- App Main Code ---
load_dotenv()
API_BASE_URL = "http://127.0.0.1:5000"

# --- 0. Sidebar Interface ---
st.sidebar.header("🧠 Living Memory")
st.sidebar.caption("Add new knowledge to the AI's brain.")

# --- Section 1: Add Note by Text ---
st.sidebar.subheader("Add a Text Note")
new_note_content = st.sidebar.text_area("New Note:", height=100, key="new_note_area", label_visibility="collapsed", placeholder="Type your new knowledge here...")

if st.sidebar.button("💾 Save & Update Memory", key="save_note", help="Saves the text note and rebuilds the AI's knowledge base"):
    if new_note_content.strip():
        with st.spinner("Saving note and updating memory..."):
            try:
                response = requests.post(f"{API_BASE_URL}/add_note", json={"content": new_note_content})
                response.raise_for_status()
                data = response.json()
                if data.get("success"):
                    st.sidebar.success(data.get("message", "Memory updated!"))
                    st.rerun() 
                else:
                    st.sidebar.error(data.get("error", "Unknown error occurred"))
            except requests.exceptions.ConnectionError:
                st.sidebar.error(f"API Connection Error. Is api.py running?")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.warning("Note cannot be empty.")

st.sidebar.divider()

# --- NEW Section 2: Add Note by File ---
st.sidebar.subheader("Upload a File")
uploaded_file = st.sidebar.file_uploader("Upload (.txt, .md, .pdf, .docx)", type=["txt", "md", "pdf", "docx"], label_visibility="collapsed")

if uploaded_file is not None:
    if st.sidebar.button("📤 Upload & Update Memory", key="upload_file", help="Uploads the file and rebuilds the AI's knowledge base"):
        with st.spinner(f"Uploading '{uploaded_file.name}' and updating memory..."):
            try:
                files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
                response = requests.post(f"{API_BASE_URL}/upload_file", files=files)
                response.raise_for_status()
                data = response.json()
                
                if data.get("success"):
                    st.sidebar.success(data.get("message", "File uploaded!"))
                    st.rerun()
                else:
                    st.sidebar.error(data.get("error", "Unknown error occurred"))
                    
            except requests.exceptions.ConnectionError:
                st.sidebar.error(f"API Connection Error. Is api.py running?")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

st.sidebar.divider()
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.messages = []


# --- 1. Chat History Initialization ---
st.title("CoreMind")
st.caption("Your personalized AI assistant powered by local knowledge.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. Display Chat History ---
# (Rest of the chat code is exactly the same as v0.5)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("context"):
            with st.expander("Show Sources Used"):
                for note in message["context"]:
                    st.caption(f"**(From: {note['source']})** {note['content'][:150]}...")

# --- 3. Chat Input Interface ---
if prompt := st.chat_input("Ask CoreMind..."):
    try:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        messages_to_send = [msg.copy() for msg in st.session_state.messages]
        for msg in messages_to_send:
            msg.pop('context', None) 

        with st.chat_message("assistant"):
            with st.spinner("CoreMind is thinking..."):
                response = requests.post(f"{API_BASE_URL}/query", json={"messages": messages_to_send})
                response.raise_for_status()
                data = response.json()

                response_text = data.get("response_text")
                found_context = data.get("found_context")

                st.markdown(response_text)

                if found_context:
                    with st.expander("Show Sources Used"):
                        for note in found_context:
                            st.caption(f"**(From: {note['source']})** {note['content'][:150]}...")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "context": found_context 
                })

    except requests.exceptions.ConnectionError:
        st.error(f"Failed to connect to CoreMind API at {API_BASE_URL}. Is api.py running?")
    except Exception as e:
        st.error(f"An error occurred: {e}")