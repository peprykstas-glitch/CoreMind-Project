import streamlit as st
import requests
import time

# Configuration
API_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="CoreMind v2.1", page_icon="🧠", layout="wide")

# --- Custom CSS (Cyberpunk/Pro) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    
    /* Chat bubbles */
    .stChatMessage {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 12px;
    }
    
    /* Metrics box */
    .metric-box {
        font-size: 0.8em;
        color: #10b981;
        margin-bottom: 5px;
    }

    /* Sidebar tweaks */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #374151;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Controls & Data ---
with st.sidebar:
    st.title("🧠 CoreMind Control")
    
    # 1. LLM Settings
    st.subheader("⚙️ Generation Settings")
    temperature = st.slider("Creativity (Temperature)", 0.0, 1.0, 0.3, 0.1, help="0.0 = Precise/Factual, 1.0 = Creative/Random")
    
    # 2. Document Upload
    st.subheader("📂 Knowledge Base")
    uploaded_file = st.file_uploader("Add Context (PDF/TXT)", type=["pdf", "txt", "md"])
    
    if uploaded_file and st.button("🚀 Index Document"):
        with st.spinner("Processing..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                res = requests.post(f"{API_URL}/upload", files=files)
                if res.status_code == 200:
                    st.success(f"Indexed! ID: {res.json()['doc_id'][:8]}...")
                else:
                    st.error(f"Error: {res.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

    st.divider()
    
    # 3. Actions
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    # System Status
    try:
        health = requests.get(f"{API_URL}/health", timeout=2).json()
        st.caption(f"🟢 System Online | Model: {health['model']}")
    except:
        st.caption("🔴 System Offline")

# --- Main Interface ---
st.title("CoreMind Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Show metadata if available (Latency, Sources)
        if msg.get("latency"):
            st.markdown(f"<div class='metric-box'>⏱️ Latency: {msg['latency']:.2f}s</div>", unsafe_allow_html=True)
            
        if msg.get("sources"):
            with st.expander(f"📚 {len(msg['sources'])} Sources Used"):
                for src in msg["sources"]:
                    st.markdown(f"**{src['filename']}**: _{src['content']}_")

# Input
if prompt := st.chat_input("Type your query..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Thinking...")
        
        try:
            # Prepare payload with Temperature
            payload = {
                "messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] != "system"],
                "temperature": temperature
            }
            
            # API Call
            response = requests.post(f"{API_URL}/query", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                bot_text = data["response_text"]
                
                placeholder.markdown(bot_text)
                
                # Update history with full metadata
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": bot_text,
                    "sources": data.get("sources", []),
                    "latency": data.get("latency", 0.0)
                })
                st.rerun() # Refresh to show metrics cleanly
            else:
                placeholder.error(f"API Error: {response.text}")
                
        except Exception as e:
            placeholder.error(f"Network Error: {e}")