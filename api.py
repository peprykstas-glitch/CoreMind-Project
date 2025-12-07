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

# Import our refactored memory utilities
from memory_utils import build_index_from_scratch, load_embedding_model, add_document_to_index

print("Starting CoreMind API (v1.2 - Stable)...")

# --- 1. Load Config ---
load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434/v1")
OLLAMA_MODEL_NAME = "gemma:2b" 
DATA_DIR = "./data"
DB_PATH = os.path.join(DATA_DIR, "chat_logs.db")

# --- 2. Database Setup ---
def init_db():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Table with feedback column
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  timestamp TEXT, 
                  user_query TEXT, 
                  bot_response TEXT, 
                  intent TEXT,
                  latency REAL,
                  feedback INTEGER DEFAULT 0)''') 
    conn.commit()
    conn.close()

init_db()

# --- 3. Load Models ---
try:
    print("Loading embedding model...")
    embed_model = load_embedding_model() 
    print(f"Connecting to Ollama at {OLLAMA_HOST}...")
    client = OpenAI(base_url=OLLAMA_HOST, api_key='ollama')
    client.models.list() # Health check
    print("Connected to Ollama!")
except Exception as e:
    print(f"!!! OLLAMA ERROR: {e}")

# --- 4. Initialize Memory ---
index = None
notes = []

def initialize_memory():
    global index, notes
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    if not os.path.exists("my_faiss.index") or not os.path.exists("my_notes.json"):
        build_index_from_scratch(DATA_DIR)
    try:
        index = faiss.read_index("my_faiss.index")
        with open('my_notes.json', 'r', encoding='utf-8') as f:
            notes = json.load(f)
        print(f"Memory loaded. {len(notes)} docs.")
    except:
        index = None; notes = []

initialize_memory()

app = Flask(__name__)
CORS(app) 

# --- 5. Helper Functions (DEFINED BEFORE USE) ---

def search_in_memory(query, k=3):
    """Searches FAISS index for relevant notes."""
    global index, notes
    if not index or not notes: return []
    
    k = min(k, len(notes))
    if k == 0: return []
    
    query_vector = embed_model.encode([query], normalize_embeddings=True)
    distances, indices = index.search(query_vector, k)
    
    # Filter out invalid indices
    valid_results = [notes[i] for i in indices[0] if 0 <= i < len(notes)]
    return valid_results

def get_query_intent(user_prompt):
    return "SEARCH"

# --- 6. API Endpoints ---

@app.route('/query', methods=['POST'])
def handle_query():
    start_time = time.time()
    data = request.json
    messages = data.get('messages')
    
    if not messages: return jsonify({"error": "No messages"}), 400

    user_query = messages[-1]['content']
    
    # 1. Search Context
    context_notes = search_in_memory(user_query) # <--- NOW IT IS DEFINED ABOVE
    found_context_data = context_notes if context_notes else []
    
    if context_notes:
        context_str = "\n".join([f"- {n['content']}" for n in context_notes])
    else:
        context_str = "No specific context found."

    # 2. Generate Answer (Aggressive Prompt)
    system_prompt = (
        "You are CoreMind. Use this INTERNAL KNOWLEDGE BASE to answer. "
        "The info is NOT private. If there is a name, state it. "
        f"\n\n--- KNOWLEDGE BASE ---\n{context_str}"
    )
    
    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL_NAME, 
            messages=[{"role": "user", "content": system_prompt + "\n\nQuestion: " + user_query}],
            temperature=0.1
        )
        bot_text = response.choices[0].message.content
    except Exception as e:
        bot_text = f"Error: {e}"

    # 3. Log Analytics
    latency = time.time() - start_time
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO logs (timestamp, user_query, bot_response, intent, latency) VALUES (?, ?, ?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_query, bot_text, "SEARCH", latency))
    log_id = c.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "response_text": bot_text, 
        "found_context": found_context_data,
        "log_id": log_id
    })

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    data = request.json
    log_id = data.get('log_id')
    score = data.get('score')
    
    if not log_id or score not in [1, -1]:
        return jsonify({"error": "Invalid data"}), 400
        
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE logs SET feedback = ? WHERE id = ?", (score, log_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    data = request.json
    content = data.get('content')
    if not content: return jsonify({"error": "Empty"}), 400
    
    filename = f"note_{int(time.time())}.txt"
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f: f.write(content)
    
    success, msg, new_index, new_notes = add_document_to_index(filepath, index, notes)
    if success:
        index = new_index; notes = new_notes
        return jsonify({"success": True, "message": "Saved"}), 201
    return jsonify({"error": msg}), 500

@app.route('/upload_file', methods=['POST'])
def upload_file():
    global index, notes
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "No name"}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(DATA_DIR, filename)
    file.save(filepath)
    
    success, msg, new_index, new_notes = add_document_to_index(filepath, index, notes)
    if success:
        index = new_index; notes = new_notes
        return jsonify({"success": True, "message": "Uploaded"}), 201
    return jsonify({"error": msg}), 500

@app.route('/admin/rebuild_index', methods=['POST'])
def force_rebuild():
    global index, notes
    success, msg = build_index_from_scratch(DATA_DIR)
    if success:
        initialize_memory()
        return jsonify({"success": True, "message": msg})
    else:
        return jsonify({"success": False, "error": msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)