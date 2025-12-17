import streamlit as st
import requests
import pandas as pd
import os

# Configuration
API_URL = "http://127.0.0.1:8000"
LOG_FILE = "chat_logs.csv" # Path to the log file created by backend

st.set_page_config(page_title="CoreMind AI", page_icon="🧠", layout="wide")

# --- Custom CSS (Cyberpunk/Pro) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stChatMessage { background-color: #1f2937; border: 1px solid #374151; border-radius: 12px; }
    section[data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #374151; }
    
    /* Metrics Style */
    div[data-testid="stMetricValue"] { font-size: 24px; color: #10b981; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Navigation & Controls ---
with st.sidebar:
    st.title("🧠 CoreMind Admin")
    
    # NAVIGATION SWITCHER
    page = st.radio("Navigation", ["💬 Chat Interface", "📊 Analytics Dashboard"])
    
    st.divider()

    if page == "💬 Chat Interface":
        st.subheader("⚙️ Settings")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.3)
        
        st.subheader("📂 Knowledge Base")
        uploaded_file = st.file_uploader("Add Context", type=["pdf", "txt", "md"])
        if uploaded_file and st.button("🚀 Index"):
            with st.spinner("Indexing..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    res = requests.post(f"{API_URL}/upload", files=files)
                    if res.status_code == 200:
                        st.success("Indexed!")
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        if st.button("🗑️ Clear History"):
            st.session_state.messages = []
            st.rerun()

# ==========================================
# PAGE 1: CHAT INTERFACE
# ==========================================
if page == "💬 Chat Interface":
    st.title("CoreMind Assistant v1.2")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander(f"📚 Sources"):
                    for src in msg["sources"]: st.markdown(f"- {src['filename']}")

    # Input
    if prompt := st.chat_input("Type query..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("Thinking...")
            try:
                payload = {"messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] != "system"], "temperature": temperature}
                res = requests.post(f"{API_URL}/query", json=payload)
                
                if res.status_code == 200:
                    data = res.json()
                    bot_text = data["response_text"]
                    placeholder.markdown(bot_text)
                    st.session_state.messages.append({
                        "role": "assistant", "content": bot_text, 
                        "sources": data.get("sources", []), 
                        "latency": data.get("latency", 0),
                        "query_id": data.get("query_id", "0"),
                        "last_query": prompt
                    })
                    st.rerun()
                else:
                    placeholder.error(f"API Error: {res.text}")
            except Exception as e:
                placeholder.error(f"Error: {e}")

    # Feedback Loop
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        last_msg = st.session_state.messages[-1]
        col1, col2, _ = st.columns([1,1,12])
        with col1:
            if st.button("👍"):
                requests.post(f"{API_URL}/feedback", json={"query_id": last_msg.get("query_id"), "feedback": "positive", "query": last_msg.get("last_query"), "response": last_msg["content"], "latency": last_msg.get("latency")})
                st.toast("Saved (+)")
        with col2:
            if st.button("👎"):
                requests.post(f"{API_URL}/feedback", json={"query_id": last_msg.get("query_id"), "feedback": "negative", "query": last_msg.get("last_query"), "response": last_msg["content"], "latency": last_msg.get("latency")})
                st.toast("Saved (-)")

# ==========================================
# PAGE 2: ANALYTICS DASHBOARD
# ==========================================
elif page == "📊 Analytics Dashboard":
    st.title("📊 System Analytics")
    
    # Check if logs exist
    if os.path.exists(LOG_FILE):
        try:
            # Load Data
            df = pd.read_csv(LOG_FILE)
            
            # --- KPI ROW ---
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Queries", len(df))
            with col2:
                avg_lat = df["Latency"].mean() if not df.empty else 0
                st.metric("Avg Latency", f"{avg_lat:.2f}s")
            with col3:
                likes = len(df[df["Feedback"] == "positive"])
                st.metric("👍 Likes", likes)
            with col4:
                dislikes = len(df[df["Feedback"] == "negative"])
                st.metric("👎 Dislikes", dislikes)
            
            st.divider()
            
            # --- CHARTS ---
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("⏱️ Latency History")
                # Line chart of latency over requests
                st.line_chart(df["Latency"])
            
            with c2:
                st.subheader("🧠 Model Usage")
                # Bar chart of models used
                st.bar_chart(df["Model"].value_counts())

            # --- RAW DATA TABLE ---
            st.subheader("📝 Recent Logs")
            # Show last 10 logs, latest first
            st.dataframe(df.sort_index(ascending=False).head(10), use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading logs: {e}")
    else:
        st.warning("No data yet. Go to 'Chat Interface' and ask some questions!")