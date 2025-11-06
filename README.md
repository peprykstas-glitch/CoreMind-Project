# CoreMind v0.4 (Private AI Knowledge Assistant)

This is a functional prototype of a 100% private, local-first AI assistant designed to answer questions based on a private knowledge base (RAG).

This project was built to solve a real-world business problem: providing instant, accurate answers to staff questions based on internal company documents (FAQs, procedures, etc.) while ensuring 100% data privacy.

### Core Architecture (Backend + Frontend)

This project uses a decoupled architecture, making it highly flexible and scalable:

1.  **Backend (`api.py`):** A **Flask API** that serves as the "brain". It handles:
    * **AI Processing:** Connects to a local LLM via **Ollama (Llama 3.1)**.
    * **Memory (RAG):** Uses **FAISS** and **SentenceTransformers** to create and search a vector index of all documents in the `/data` folder.
    * **Logic:** Features an intelligent "Query Router" to distinguish between chit-chat and knowledge-based questions.
2.  **Frontend (`app.py`):** A **Streamlit** UI that acts as the "face" of the application. It provides:
    * A clean, real-time chat interface.
    * Chat history (`st.session_state`).
    * A "Living Memory" interface to upload new notes and rebuild the AI's knowledge base via API calls.

### Technologies Used

* **Python**
* **Backend:** Flask, Ollama, OpenAI (client)
* **RAG/AI:** FAISS (faiss-cpu), SentenceTransformers
* **Frontend:** Streamlit
* **Utils:** python-dotenv, requests

### How to Run

1.  **Prerequisite:** Ensure you have **Ollama** installed and have run `ollama run llama3.1:8b`.
2.  **Install dependencies:** `pip install -r requirements.txt`
3.  **Run the Backend (Terminal 1):** `python api.py`
4.  **Run the Frontend (Terminal 2):** `streamlit run app.py`