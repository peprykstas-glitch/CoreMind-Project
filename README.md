# 🧠 Vectrieve AI (v2.0)

**Vectrieve** is a secure, local RAG (Retrieval-Augmented Generation) Knowledge Assistant designed for developers and product managers. It allows users to chat with their documents (PDF, TXT) and source code (Python, JS, TS) with high precision and zero data leakage.

![Vectrieve UI Screenshot](![alt text](image.png))
*(Replace this link with your actual screenshot)*

## 🚀 Key Features

-   **🔍 Chat with Codebase:** Drag & drop project files (`.py`, `.js`, `.tsx`) to analyze logic, architecture, and endpoints instantly.
-   **📄 Document Intelligence:** Powered by **Qdrant** vector search to retrieve precise context from large PDFs.
-   **📊 Analytics Dashboard:** Real-time tracking of latency, model usage, and user feedback (👍/👎).
-   **⚡ High Performance:** Built on **FastAPI** (Backend) and **Next.js 14** (Frontend) with optimized memory management.
-   **🛡️ Secure & Local:** Documents are processed locally and stored in a Dockerized vector database.

## 🛠️ Tech Stack

-   **Core AI:** Groq (Llama-3-70b-versatile)
-   **Vector DB:** Qdrant (Docker)
-   **Backend:** Python, FastAPI, Pandas
-   **Frontend:** TypeScript, Next.js, Tailwind CSS, Recharts
-   **Orchestration:** Docker Compose

## 📦 Installation Guide

### Prerequisites
-   Docker Desktop installed & running
-   Python 3.10+
-   Node.js 18+

### 1. Clone & Setup Database
```bash
git clone [https://github.com/your-username/vectrieve-ai.git](https://github.com/your-username/vectrieve-ai.git)
cd vectrieve-ai
docker-compose up -d  # Starts Qdrant Vector DB
2. Backend Setup (Brain)
Bash

cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
python main.py
# Server starts at http://localhost:8000
3. Frontend Setup (UI)
Bash

cd vectrieve-ui
npm install
npm run build
npm start
# UI opens at http://localhost:3000
🧩 How It Works
Ingestion: User uploads a file. The backend parses text/code, chunks it, creates embeddings, and stores them in Qdrant.

Retrieval: When a user asks a question, the system searches for the most relevant chunks in the vector DB.

Generation: The retrieved context + user query are sent to the LLM (Groq) to generate a grounded response.

🤝 Contribution
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Created by Stanislav Pepryk