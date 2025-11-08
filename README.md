# CoreMind v0.6 (Private AI Knowledge Assistant)
This is a functional prototype of a 100% private, local-first AI assistant designed to answer questions based on a private, local knowledge base (RAG).

This project was built to solve a real-world business problem: providing instant, accurate answers to staff questions based on internal company documents (FAQs, procedures, CVs, etc.) while ensuring 100% data privacy.

Core Features
100% Private: Uses a local LLM (Ollama) for all processing. No data ever leaves the machine.

Knowledge Base (RAG): Connects to a local folder (/data) and uses a FAISS vector index to find relevant information.

Multi-Format Support: Can read and index text from .txt, .md, .pdf, and .docx files.

Living Memory: Features a UI to add new text notes or upload files directly, with instant rebuilding of the AI's memory.

Smart Routing: Includes an intelligent "Query Router" to distinguish between simple chit-chat and questions that require a knowledge base search.

Core Architecture (Backend + Frontend)
This project uses a decoupled architecture for flexibility:

Backend (api.py): A Flask API that serves as the "brain". It handles:

AI Processing: Connects to a local LLM via Ollama (Llama 3.1).

Memory (RAG): Uses FAISS and SentenceTransformers to create and search a vector index.

File Parsing: Uses pypdf and python-docx to extract text from uploaded files.

Endpoints: Provides routes for /query, /add_note, and /upload_file.

Frontend (app.py): A Streamlit UI that acts as the "face". It provides:

A clean, real-time chat interface with a custom dark theme.

Chat history (st.session_state).

A "Living Memory" sidebar to add new text notes or upload files to the backend.

Technologies Used
Python

Backend: Flask, Ollama, OpenAI (client library)

RAG/AI: FAISS (faiss-cpu), SentenceTransformers

File Parsing: pypdf, python-docx

Frontend: Streamlit

Utils: python-dotenv, requests

How to Run
Prerequisite (AI Model):

Install Ollama from ollama.com.

Pull the model: ollama run llama3.1:8b (or another model like gemma:2b if you have low RAM).

Ensure Ollama is running in the background.

Prerequisite (Python Setup):

Create a virtual environment: python -m venv venv

Activate it: .\venv\Scripts\Activate.ps1

Install dependencies: pip install -r requirements.txt

Run the Backend (Terminal 1):

(venv) python api.py

Wait for it to connect to Ollama and show Running on http://127.0.0.1:5000...

Run the Frontend (Terminal 2):

(venv) streamlit run app.py