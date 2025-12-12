# 🧠 CoreMind: Private AI Knowledge Assistant

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-orange)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)

> **A local-first RAG (Retrieval-Augmented Generation) system tailored for secure document analysis without data leaks.**

---

## 🚀 Overview

CoreMind is an AI-powered assistant designed for legal and financial professionals who need to analyze sensitive documents (PDFs, contracts, reports) without uploading data to the public cloud. 

Unlike standard tools (ChatGPT, Claude), CoreMind runs **entirely locally** (or in a private cloud), ensuring 100% data privacy. It leverages **Llama 3.2** for reasoning and **Qdrant** for semantic search.

### 🎯 Key Features
* **🔒 Privacy First:** Your documents never leave your infrastructure.
* **📚 RAG Architecture:** Answers are grounded in your specific documents, reducing hallucinations.
* **⚡ Async Backend:** Built on FastAPI for high-throughput and non-blocking operations.
* **🎛️ User Control:** Adjustable LLM temperature (Creativity vs. Precision) via the UI.
* **🕵️‍♂️ Transparent AI:** Shows source citations and latency metrics for every response.

---

## 🏗️ Technical Architecture

The project follows a modular, microservices-ready architecture:

1.  **Frontend:** Streamlit (Python) - Provides a chat interface and control panel.
2.  **Backend:** FastAPI - Orchestrates data processing, parsing, and LLM communication.
3.  **Vector Database:** Qdrant (Docker) - Stores document embeddings for semantic search.
4.  **Inference Engine:** Ollama (Local) - Runs the Llama 3.2 3B model.

### 🛠 Tech Stack
* **Language:** Python 3.11
* **Frameworks:** FastAPI, Streamlit
* **AI/ML:** LangChain (concepts), Ollama, FastEmbed
* **Database:** Qdrant (via Docker Compose)
* **DevOps:** Docker

---

## ⚡ Quick Start

### Prerequisites
* Docker & Docker Compose installed.
* Python 3.10+ installed.
* [Ollama](https://ollama.com/) installed and running.

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/CoreMind.git](https://github.com/YOUR_USERNAME/CoreMind.git)
cd CoreMind
2. Start the Vector Database
We use Docker for the database to keep the host system clean.

Bash

docker-compose up -d qdrant
3. Setup Backend (The Brain)
Open a terminal:

Bash

# Create virtual environment (optional but recommended)
python -m venv venv
# Activate it (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API
python backend/main.py
4. Setup Frontend (The UI)
Open a new terminal:

Bash

streamlit run frontend/main.py
👉 Access the app at: http://localhost:8501

📸 Screenshots
(Add screenshots of your Dark UI here later)

🔮 Roadmap
[x] MVP: Local RAG with Llama 3.2.

[x] UI v2: Dark Mode & Settings Panel.

[ ] Hybrid Mode: Switch between Local Ollama and Cloud (Groq/OpenAI) for heavier tasks.

[ ] Active Draft: Split-screen mode for real-time document co-authoring.

[ ] Multi-Format Support: Parsing for .docx and .pptx files.

🤝 Contributing
This project is a Proof of Concept (PoC) for a secure enterprise AI solution. Feedback and Pull Requests are welcome!

📄 License
MIT License.