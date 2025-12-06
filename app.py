import streamlit as st
import requests
import os
from dotenv import load_dotenv

# --- 0. Page Config ---
st.set_page_config(
    page_title="CoreMind v0.8",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Block ---
st.markdown("""
<style>
    /* Dark Theme Optimization */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stTextInput > div > div > input { color: #FAFAFA; background-color: #262730; }
    .stTextArea > div > div > textarea { color: #FAFAFA; background-color: #262730; }
    .stButton > button { background-color: #FF4B4B; color: white; border-radius: 5px; }
    div[data-testid="stExpander"] div[role="button"] p { font-size: 1.1rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- Config ---
load_dotenv()
# В Docker ми будемо передавати це як змінну середовища. 
# За замовчуванням (локально) - http://127.0.0.1:5000
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")

# --- Sidebar ---
st.sidebar.header("🧠 Living Memory")
st.sidebar.caption(f"Backend: {API_BASE_URL}")

# --- Add Note ---
st.sidebar.subheader("Add a Text Note")
new_note_content = st.sidebar.text_area("New Note:", height=100, key="new_note_area", label_visibility="collapsed", placeholder="Type new knowledge...")

if st.sidebar.button("💾 Save to Memory", key="save_note"):
    if new_note_content.strip():
        with st.spinner("Indexing..."):
            try:
                response = requests.post(f"{API_BASE_URL}/add_note", json={"content": new_note_content})
                if response.status_code == 201:
                    st.sidebar.success("Memory updated!")
                    st.rerun()
                else:
                    st.sidebar.error(f"Error: {response.json().get('error')}")
            except Exception as e:
                st.sidebar.error(f"Connection Error: {e}")

st.sidebar.divider()

# --- Upload File ---
st.sidebar.subheader("Upload File")
uploaded_file = st.sidebar.file_uploader("Format: .txt, .pdf, .docx", type=["txt", "md", "pdf", "docx"])

if uploaded_file is not None:
    if st.sidebar.button("📤 Upload & Index"):
        with st.spinner("Processing..."):
            try:
                files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
                response = requests.post(f"{API_BASE_URL}/upload_file", files=files)
                if response.status_code == 201:
                    st.sidebar.success("File indexed!")
                    st.rerun()
                else:
                    st.sidebar.error(f"Error: {response.json().get('error')}")
            except Exception as e:
                st.sidebar.error(f"Connection Error: {e}")

st.sidebar.divider()

# --- Admin Tools ---
with st.sidebar.expander("🛠 Admin Tools"):
    if st.button("♻️ Force Full Rebuild"):
        with st.spinner("Rebuilding index from scratch..."):
            try:
                res = requests.post(f"{API_BASE_URL}/admin/rebuild_index")
                if res.status_code == 200:
                    st.success("Rebuild complete!")
                else:
                    st.error("Rebuild failed.")
            except Exception as e:
                st.error(f"Error: {e}")

if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []


# --- Main Chat Interface ---
st.title("CoreMind")
st.caption("Secure Local RAG System")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("context"):
            with st.expander("📚 Sources"):
                for note in message["context"]:
                    st.caption(f"**{note['source']}**: {note['content'][:150]}...")

# Input
if prompt := st.chat_input("Ask something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    messages_to_send = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(f"{API_BASE_URL}/query", json={"messages": messages_to_send})
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response_text")
                    found_context = data.get("found_context")

                    st.markdown(response_text)
                    if found_context:
                        with st.expander("📚 Sources"):
                            for note in found_context:
                                st.caption(f"**{note['source']}**: {note['content'][:150]}...")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "context": found_context
                    })
                else:
                    st.error(f"API Error: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error(f"Cannot connect to CoreMind API at {API_BASE_URL}")