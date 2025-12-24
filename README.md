# 🧠 Vectrieve AI: Context-Aware RAG Assistant

> **An advanced AI assistant that builds a "Second Brain" from your documents.** > Features: OCR (Vision), Conversational Memory, and Analytics Dashboard.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-ff4b4b)
![Groq](https://img.shields.io/badge/AI-Groq%20LPU-orange)
![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-red)

## 📖 Project Overview

**Vectrieve** is a full-stack RAG (Retrieval-Augmented Generation) application designed to bridge the gap between static documents and interactive AI. Unlike standard chatbots, Vectrieve allows users to build a personal knowledge base by uploading PDFs, text files, and **images (via OCR)**.

Built with a focus on **Product Management principles**, the system includes a Feedback Loop (Like/Dislike), an Analytics Dashboard to track KPI (Latency, Token Usage), and a robust Admin Interface.

## ✨ Key Features

### 🚀 Core Functionality
* **RAG Pipeline:** Retrieves precise answers from your own documents using **Qdrant** (Vector Search).
* **LLM Powerhouse:** Powered by **Meta Llama 3.3 (70B)** via **Groq LPU** for lightning-fast inference (<1s latency).
* **Computer Vision (OCR):** Extracts text from images and scanned documents using **Tesseract OCR**.
* **Context Awareness:** Remembers chat history and resolves references (e.g., "Where does *he* live?").

### 📊 Admin & Analytics (PM Features)
* **Analytics Dashboard:** Visualizes system performance (Latency trends, Query volume, Model usage).
* **Feedback Loop:** Users can rate responses (👍/👎), creating a dataset for future improvements.
* **Knowledge Management:** UI to view indexed files and delete outdated documents from the vector database.

### 🎭 Adaptive Persona
* **Strict Mode:** Professional and precise for technical queries based on docs.
* **Creative Mode:** Witty and sarcastic (Storyteller persona) for general chit-chat.

---

## 🏗️ Architecture



The system follows a microservices-like architecture:
1.  **Frontend (Streamlit):** Handles UI, Session State, and Visualization.
2.  **Backend (FastAPI):** Manages API endpoints, File Parsing, and Business Logic.
3.  **Vector Store (Qdrant):** Stores document embeddings for semantic search.
4.  **Inference Engine (Groq):** Generates human-like responses based on retrieved context.

---

## 🛠️ Tech Stack

* **Language:** Python 3.11
* **Backend:** FastAPI, Pydantic, Uvicorn
* **Frontend:** Streamlit, Pandas (for Analytics)
* **AI & ML:** * **LLM:** Llama 3.3-70b-versatile (via Groq API)
    * **Embeddings:** FastEmbed / HuggingFace
    * **OCR:** Tesseract + Pytesseract + Pillow
* **Database:** Qdrant (Local Docker instance or Embedded)
* **Tools:** Git, Python-dotenv

---

## 📸 Screenshots

### 1. Chat Interface with OCR Support
> Vectrieve analyzing an image and extracting text.
*(Place your screenshot here, e.g., `![Chat](screenshots/chat_ocr.png)`)*

### 2. Analytics Dashboard
> Monitoring system latency and user feedback.
*(Place your screenshot here, e.g., `![Dashboard](screenshots/dashboard.png)`)*

### 3. Knowledge Management
> Managing uploaded files and vector index.
*(Place your screenshot here, e.g., `![Memory](screenshots/memory.png)`)*

---

## 🚀 How to Run

### Prerequisites
* Python 3.10+
* [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed on your machine.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/Vectrieve.git](https://github.com/YOUR_USERNAME/Vectrieve.git)
    cd Vectrieve
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment:**
    Create a `.env` file in the root directory:
    ```env
    GROQ_API_KEY=gsk_your_key_here
    PROJECT_NAME=Vectrieve AI
    VERSION=1.4
    ```

4.  **Run the System:**
    * **Backend:**
        ```bash
        python backend/main.py
        ```
    * **Frontend:**
        ```bash
        streamlit run frontend/main.py
        ```

---

## 🔮 Roadmap

* [ ] **Cloud Deployment:** Dockerize and deploy to AWS/Render.
* [ ] **Voice Interface:** Speech-to-Text integration for voice commands.
* [ ] **Advanced Parsing:** Better handling of complex tables in PDFs.
* [ ] **Multi-User Auth:** Login system for team usage.

---

## 👤 Author

**Stanislav Pepryk** *Business Management Student | Aspiring IT Project Manager & Product Owner*

Passionate about bridging the gap between Business goals and Technical implementation through AI & Automation.

[LinkedIn](www.linkedin.com/in/stanislav-pepryk-0139802b6) | [GitHub](https://github.com/peprykstas-glitch)