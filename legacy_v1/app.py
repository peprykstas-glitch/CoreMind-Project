import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

# --- Page Config ---
st.set_page_config(
    page_title="CoreMind AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    /* Стиль для метрик */
    div[data-testid="stMetricValue"] { font-size: 24px; color: #FF4B4B; }
</style>
""", unsafe_allow_html=True)

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")

if "messages" not in st.session_state: st.session_state.messages = []

# --- Sidebar Navigation ---
st.sidebar.title("🧠 CoreMind")
# Тепер тут 3 пункти, як має бути
page = st.sidebar.radio("Navigation", ["Chat", "Analytics", "Knowledge Base"])
st.sidebar.caption(f"Backend: {API_BASE_URL}")

# ==========================================
# PAGE 1: CHAT (Спілкування + Фідбек)
# ==========================================
if page == "Chat":
    st.header("💬 Intelligent Assistant")
    
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()

    # Display Chat History
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Show sources (Context)
            if msg.get("context"):
                with st.expander("📚 Sources used"):
                    for note in msg["context"]:
                        st.caption(f"**{note['source']}**: {note['content'][:150]}...")
            
            # Show Feedback Buttons (Only for Assistant)
            if msg["role"] == "assistant" and msg.get("log_id"):
                col1, col2, col3 = st.columns([1, 1, 10])
                with col1:
                    if st.button("👍", key=f"like_{i}"):
                        try:
                            requests.post(f"{API_BASE_URL}/feedback", json={"log_id": msg["log_id"], "score": 1})
                            st.toast("Feedback saved!", icon="✅")
                        except: st.error("API Error")
                with col2:
                    if st.button("👎", key=f"dislike_{i}"):
                        try:
                            requests.post(f"{API_BASE_URL}/feedback", json={"log_id": msg["log_id"], "score": -1})
                            st.toast("Feedback saved!", icon="✅")
                        except: st.error("API Error")

    # Input Area
    if prompt := st.chat_input("Ask a question based on your knowledge base..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing documents..."):
                try:
                    res = requests.post(f"{API_BASE_URL}/query", json={"messages": st.session_state.messages})
                    if res.status_code == 200:
                        data = res.json()
                        bot_text = data.get("response_text", "No response")
                        log_id = data.get("log_id")
                        context = data.get("found_context")
                        
                        st.markdown(bot_text)
                        
                        # Save to history
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": bot_text,
                            "context": context,
                            "log_id": log_id 
                        })
                        st.rerun() # Refresh to show buttons
                    else:
                        st.error(f"Backend Error: {res.text}")
                except Exception as e:
                    st.error(f"Connection Error. Is Backend running? {e}")

# ==========================================
# PAGE 2: ANALYTICS (Метрики + Графіки)
# ==========================================
elif page == "Analytics":
    st.header("📊 Quality Dashboard")
    if st.button("🔄 Refresh Data"): st.rerun()
    
    try:
        res = requests.get(f"{API_BASE_URL}/analytics")
        data = res.json().get("logs", [])
        
        if data:
            df = pd.DataFrame(data, columns=["ID", "Timestamp", "Query", "Response", "Intent", "Latency", "Feedback"])
            
            # Metrics Calculation
            total = len(df)
            positive = df[df["Feedback"] == 1].shape[0]
            rated = df[df["Feedback"] != 0].shape[0]
            csat = (positive / rated * 100) if rated > 0 else 0
            avg_latency = df['Latency'].mean()
            
            # Top Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Queries", total)
            m2.metric("Feedback Count", rated)
            m3.metric("CSAT Score", f"{csat:.0f}%", delta=f"{positive} likes")
            m4.metric("Avg Latency", f"{avg_latency:.2f}s")
            
            st.divider()
            
            # Charts
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Latency Trend")
                st.line_chart(df["Latency"])
            with c2:
                st.subheader("Feedback Distribution")
                st.bar_chart(df["Feedback"].value_counts())

            # Raw Data
            st.subheader("Recent Logs")
            st.dataframe(df.sort_values(by="ID", ascending=False))
        else:
            st.info("No analytics data yet. Go chat first!")
            
    except Exception as e:
        st.error(f"Analytics Error: {e}")

# ==========================================
# PAGE 3: KNOWLEDGE BASE (Те, що зникло!)
# ==========================================
elif page == "Knowledge Base":
    st.header("📂 Knowledge Management")
    st.caption("Add data here to make the AI smarter.")
    
    tab1, tab2, tab3 = st.tabs(["📝 Add Text Note", "📤 Upload File", "⚙️ Admin Tools"])
    
    # 1. Text Note
    with tab1:
        note_content = st.text_area("Content:", height=200, placeholder="Paste text here...")
        if st.button("Save Text Note"):
            if note_content.strip():
                with st.spinner("Indexing..."):
                    try:
                        res = requests.post(f"{API_BASE_URL}/add_note", json={"content": note_content})
                        if res.status_code == 201:
                            st.success("Note saved and indexed!")
                        else:
                            st.error(f"Error: {res.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Content cannot be empty.")

    # 2. File Upload
    with tab2:
        uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"])
        if uploaded_file is not None:
            if st.button("Upload & Index File"):
                with st.spinner("Uploading and processing..."):
                    try:
                        files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
                        res = requests.post(f"{API_BASE_URL}/upload_file", files=files)
                        if res.status_code == 201:
                            st.success(f"File '{uploaded_file.name}' indexed successfully!")
                        else:
                            st.error(f"Error: {res.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # 3. Admin Tools (Rebuild)
    with tab3:
        st.warning("Use this if search isn't working correctly.")
        if st.button("⚠️ Force Full Rebuild"):
            with st.spinner("Rebuilding entire index..."):
                try:
                    res = requests.post(f"{API_BASE_URL}/admin/rebuild_index")
                    if res.status_code == 200:
                        st.success("Index rebuilt from scratch!")
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Error: {e}")