import os
import time
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI 
from werkzeug.utils import secure_filename

# Наші утиліти
from legacy_v1.memory_utils import build_index_from_scratch, load_embedding_model, add_document_to_index

print("Starting CoreMind API (v1.4 - Optimized for 8GB RAM)...")

# --- Config ---
load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434/v1")

# ЗМІНА 1: Використовуємо Llama 3.2 3B (легка і розумна)
OLLAMA_MODEL_NAME = "llama3.2:3b" 

DATA_DIR = "./data"
DB_PATH = os.path.join(DATA_DIR, "chat_logs.db")

# --- Database ---
def init_db():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp TEXT, user_query TEXT, bot_response TEXT, 
                  intent TEXT, latency REAL, feedback INTEGER DEFAULT 0)''') 
    conn.commit()
    conn.close()

init_db()

# --- Models ---
try:
    print("Loading embedding model...")
    embed_model = load_embedding_model() 
    print(f"Connecting to Ollama at {OLLAMA_HOST}...")
    client = OpenAI(base_url=OLLAMA_HOST, api_key='ollama')
    client.models.list() 
    print(f"Connected! Target Model: {OLLAMA_MODEL_NAME}")
except Exception as e:
    print(f"!!! Error loading models: {e}")

# --- Memory ---
index = None
notes = []

def initialize_memory():
    global index, notes
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    if not os.path.exists("my_faiss.index"):
        build_index_from_scratch(DATA_DIR)
    try:
        index = faiss.read_index("my_faiss.index")
        with open('my_notes.json', 'r', encoding='utf-8') as f: notes = json.load(f)
        print(f"Memory loaded: {len(notes)} docs")
    except: index = None; notes = []

initialize_memory()

app = Flask(__name__)
CORS(app) 

# --- Functions ---
def search_in_memory(query, k=3):
    global index, notes
    if not index or not notes: return []
    k = min(k, len(notes))
    if k == 0: return []
    
    query_vector = embed_model.encode([query], normalize_embeddings=True)
    distances, indices = index.search(query_vector, k)
    return [notes[i] for i in indices[0] if 0 <= i < len(notes)]

# --- Endpoints ---

@app.route('/query', methods=['POST'])
def handle_query():
    start_time = time.time()
    data = request.json
    messages = data.get('messages')
    user_query = messages[-1]['content']
    
    context_notes = search_in_memory(user_query)
    context_str = "\n".join([f"- {n['content']}" for n in context_notes]) if context_notes else "No context."

    system_prompt = (
        "You are CoreMind. Use this KNOWLEDGE BASE to answer. "
        "The info is NOT private. If there is a name, state it. "
        f"\n\n--- KNOWLEDGE BASE ---\n{context_str}"
    )
    
    # ЗМІНА 2: Додаємо параметри для економії пам'яті (num_ctx=2048)
    # Ми передаємо це через extra_body, бо OpenAI клієнт не має прямого параметру options
    options = {
        "num_ctx": 2048,  # Обмежуємо контекст (економить RAM)
        "temperature": 0.3 # Менш хаотична
    }

    try:
        # Для Ollama через OpenAI library параметри передаються трохи хитро
        # Ми просто додамо їх, якщо бібліотека підтримує, або покладемося на дефолт Ollama
        # (Найнадійніший спосіб - налаштувати це при запуску моделі, але спробуємо так)
        
        response = client.chat.completions.create(
            model=OLLAMA_MODEL_NAME, 
            messages=[{"role": "user", "content": system_prompt + "\n\nQuestion: " + user_query}],
            # OpenAI library може ігнорувати `options`, тому ми покладаємось на те, 
            # що ти зробив `ollama run` з параметрами або просто модель легка.
            # Llama 3.2 3B сама по собі дуже легка.
            temperature=0.3
        )
        bot_text = response.choices[0].message.content
    except Exception as e: bot_text = f"Error: {e}"

    latency = time.time() - start_time
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO logs (timestamp, user_query, bot_response, intent, latency) VALUES (?, ?, ?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_query, bot_text, "SEARCH", latency))
    log_id = c.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"response_text": bot_text, "found_context": context_notes, "log_id": log_id})

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    data = request.json
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE logs SET feedback = ? WHERE id = ?", (data['score'], data['log_id']))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/analytics', methods=['GET'])
def get_analytics():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return jsonify({"logs": rows})

@app.route('/add_note', methods=['POST'])
def add_note():
    global index, notes
    content = request.json.get('content')
    filename = f"note_{int(time.time())}.txt"
    with open(os.path.join(DATA_DIR, filename), 'w', encoding='utf-8') as f: f.write(content)
    
    success, msg, new_index, new_notes = add_document_to_index(os.path.join(DATA_DIR, filename), index, notes)
    if success: index = new_index; notes = new_notes; return jsonify({"success": True}), 201
    return jsonify({"error": msg}), 500

@app.route('/upload_file', methods=['POST'])
def upload_file():
    global index, notes
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(DATA_DIR, filename)
    file.save(filepath)
    
    success, msg, new_index, new_notes = add_document_to_index(filepath, index, notes)
    if success: index = new_index; notes = new_notes; return jsonify({"success": True}), 201
    return jsonify({"error": msg}), 500

@app.route('/admin/rebuild_index', methods=['POST'])
def force_rebuild():
    success, msg = build_index_from_scratch(DATA_DIR)
    if success: initialize_memory(); return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "error": msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)