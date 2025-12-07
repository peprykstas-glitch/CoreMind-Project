import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

st.set_page_config(page_title="CoreMind AI", layout="wide")
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")

if "messages" not in st.session_state: st.session_state.messages = []

# --- Sidebar ---
page = st.sidebar.radio("Menu", ["💬 Chat", "📊 Analytics"])

if page == "💬 Chat":
    st.header("Chat with Feedback")

    # Display Chat
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Show sources if any
            if msg.get("context"):
                with st.expander("📚 Sources"):
                    for note in msg["context"]:
                        st.caption(f"**{note['source']}**: {note['content'][:100]}...")
            
            # Show Feedback Buttons (Only for Assistant messages that have a log_id)
            if msg["role"] == "assistant" and msg.get("log_id"):
                col1, col2, col3 = st.columns([1, 1, 10])
                
                # Unique key for each button is crucial!
                with col1:
                    if st.button("👍", key=f"like_{i}"):
                        requests.post(f"{API_BASE_URL}/feedback", json={"log_id": msg["log_id"], "score": 1})
                        st.toast("Thanks for positive feedback!")
                with col2:
                    if st.button("👎", key=f"dislike_{i}"):
                        requests.post(f"{API_BASE_URL}/feedback", json={"log_id": msg["log_id"], "score": -1})
                        st.toast("We'll try to improve.")

    # Input
    if prompt := st.chat_input("Ask me..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                res = requests.post(f"{API_BASE_URL}/query", json={"messages": st.session_state.messages})
                if res.status_code == 200:
                    data = res.json()
                    bot_text = data["response_text"]
                    log_id = data.get("log_id") # Get ID from backend
                    
                    st.markdown(bot_text)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": bot_text,
                        "context": data.get("found_context"),
                        "log_id": log_id 
                    })
                    st.rerun() # Refresh to show buttons immediately

elif page == "📊 Analytics":
    st.header("Quality Assurance Dashboard")
    if st.button("Refresh"): st.rerun()
    
    res = requests.get(f"{API_BASE_URL}/analytics")
    data = res.json().get("logs", [])
    if data:
        # Columns: ID, Time, Query, Response, Intent, Latency, Feedback
        df = pd.DataFrame(data, columns=["ID", "Timestamp", "Query", "Response", "Intent", "Latency", "Feedback"])
        
        # CSAT Score Calculation
        total_rated = df[df["Feedback"] != 0].shape[0]
        positive = df[df["Feedback"] == 1].shape[0]
        csat = (positive / total_rated * 100) if total_rated > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Queries", len(df))
        col2.metric("CSAT Score", f"{csat:.0f}%", help="% of Likes")
        col3.metric("Feedback Count", total_rated)
        
        st.subheader("Recent Feedback")
        # Show only rated queries
        st.dataframe(df[df["Feedback"] != 0][["Query", "Response", "Feedback"]])