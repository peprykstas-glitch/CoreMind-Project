import os
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI 
from werkzeug.utils import secure_filename

# Import our refactored memory utilities
from memory_utils import build_index_from_scratch, load_embedding_model, add_document_to_index

print("Starting CoreMind API (v0.7 - Optimized)...")

# --- 1. Load Config and Models ---
load_dotenv()
OLLAMA_MODEL_NAME = "llama3.1:8b" 
DATA_DIR = "./data"

# Global memory state
index = None
notes = []

try:
    print("Loading embedding model (for FAISS)...")
    embed_model = load_embedding_model() 
    
    print("Connecting to local Ollama server...")
    client = OpenAI(
        base_url='http://localhost:11434/v1', 
        api_key='ollama'
    )
    # Quick health check
    client.models.list()
    print(f"Successfully connected to Ollama. Using model: {OLLAMA_MODEL_NAME}")
    
except Exception as e:
    print("!!! FAILED TO CONNECT TO OLLAMA !!!")
    raise RuntimeError(f"Failed to connect to Ollama: {e}")


# --- 2. Load "Memory" (FAISS) ---
def initialize_memory():
    """
    Initializes the memory state. 
    If index exists, loads it. 
    If not, triggers a full build from scratch.
    """
    global index, notes
    print("Initializing memory...")
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    if not os.path.exists("my_faiss.index") or not os.path.exists("my_notes.json"):
        print("WARNING: Memory files not found. Building index from scratch...")
        success, msg = build_index_from_scratch(DATA_DIR)
        if not success:
            print(f"Initialization failed: {msg}")
            index = None
            notes = []
            return

    try:
        index = faiss.read_index("my_faiss.index")
        with open('my_notes.json', 'r', encoding='utf-8') as f:
            notes = json.load(f)
        print(f"Memory loaded. {len(notes)} notes indexed.")
    except Exception as e:
        print(f"Error loading existing memory: {e}")
        index = None
        notes = []

# Initialize on startup
initialize_memory()

# --- 3. Setup Flask API ---
app = Flask(__name__)
CORS(app) 

def search_in_memory(query, k=3):
    global index, notes
    if not index or not notes: return []
    
    k = min(k, len(notes))
    if k == 0: return []
    
    query_vector = embed_model.encode([query], normalize_embeddings=True)
    distances, indices = index.search(query_vector, k)
    
    # Filter out -1 indices if FAISS returns them (invalid results)
    valid_results = []
    for i in indices[0]:
        if 0 <= i < len(notes):
            valid_results.append(notes[i])
            
    return valid_results

def get_query_intent(user_prompt):
    print(f"Routing query: '{user_prompt}'")
    try:
        # Optimized prompt for the router to be faster and stricter
        router_prompt = f"Analyze: '{user_prompt}'. Return 'SEARCH' if it asks for facts/info. Return 'CHITCHAT' if it is a greeting/joke. One word only."
        response = client.chat.completions.create(model=OLLAMA_MODEL_NAME, messages=[{"role": "user", "content": router_prompt}], temperature=0.0)
        intent = response.choices[0].message.content.strip().upper()
        return "SEARCH" if "SEARCH" in intent else "CHITCHAT"
    except Exception:
        return "SEARCH" # Fail-safe

# --- Endpoint 1: Chat ---
@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    messages_from_user = data.get('messages')
    if not messages_from_user: return jsonify({"error": "Field 'messages' is required"}), 400

    try:
        current_prompt = messages_from_user[-1]['content']
        intent = get_query_intent(current_prompt)
        
        context_str = ""
        found_context_data = []

        if intent == "SEARCH":
            context_notes = search_in_memory(current_prompt)
            if context_notes:
                print(f"Found {len(context_notes)} relevant notes.")
                found_context_data = context_notes
                # Add source filename to the context sent to LLM for better citation
                context_str = "\n".join([f"Source: {n['source']}\nContent: {n['content']}" for n in context_notes])
            else:
                context_str = "No relevant internal documents found."
        else:
            context_str = "Context not needed (Chitchat)."

        system_message = {
            "role": "system",
            "content": f"""You are CoreMind, a private AI assistant. 
            Use ONLY the Context below to answer. If the answer isn't there, say you don't know.
            
            --- CONTEXT ---
            {context_str}
            ---------------
            """
        }
        
        final_messages = [system_message] + messages_from_user
        response = client.chat.completions.create(model=OLLAMA_MODEL_NAME, messages=final_messages)
        response_text = response.choices[0].message.content
        return jsonify({"response_text": response_text, "found_context": found_context_data})

    except Exception as e:
        print(f"Error during query: {e}")
        return jsonify({"error": str(e)}), 500

# --- Endpoint 2: Add Note (Optimized) ---
@app.route('/add_note', methods=['POST'])
def add_note():
    global index, notes
    data = request.json
    content = data.get('content')
    if not content or not content.strip():
        return jsonify({"error": "Note content cannot be empty"}), 400
        
    try:
        timestamp = int(time.time())
        filename = f"note_{timestamp}.txt"
        filepath = os.path.join(DATA_DIR, filename)
        
        # 1. Save file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 2. Incremental Update (Fast!)
        print(f"Adding single file to index: {filename}")
        success, msg, new_index, new_notes = add_document_to_index(filepath, index, notes)
        
        if success:
            index = new_index
            notes = new_notes
            return jsonify({"success": True, "message": f"Note added. Total: {len(notes)}"}), 201
        else:
            return jsonify({"error": msg}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Endpoint 3: Upload File (Optimized) ---
@app.route('/upload_file', methods=['POST'])
def upload_file():
    global index, notes
    if 'file' not in request.files: return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400
    
    if file:
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(DATA_DIR, filename)
            file.save(filepath)
            
            # Incremental Update (Fast!)
            print(f"Processing upload: {filename}")
            success, msg, new_index, new_notes = add_document_to_index(filepath, index, notes)
            
            if success:
                index = new_index
                notes = new_notes
                return jsonify({"success": True, "message": f"Uploaded '{filename}'. Total: {len(notes)}"}), 201
            else:
                return jsonify({"error": msg}), 500
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# --- NEW Endpoint: Force Full Rebuild (Admin) ---
@app.route('/admin/rebuild_index', methods=['POST'])
def force_rebuild():
    global index, notes
    print("Admin requested full index rebuild...")
    success, msg = build_index_from_scratch(DATA_DIR)
    if success:
        initialize_memory() # Reload globals
        return jsonify({"success": True, "message": msg})
    else:
        return jsonify({"success": False, "error": msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)