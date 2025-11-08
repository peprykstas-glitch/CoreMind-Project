import os
import os
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI 
from werkzeug.utils import secure_filename # Import for handling filenames

# Import our memory utilities
from memory_utils import build_index, load_embedding_model, extract_text_from_file

print("Starting CoreMind API (v0.6 - File Uploader)...")

# --- 1. Load Config and Models ---
load_dotenv()
OLLAMA_MODEL_NAME = "llama3.1:8b" 
DATA_DIR = "./data" # Define data directory as a constant

try:
    print("Loading embedding model (for FAISS)...")
    embed_model = load_embedding_model() 
    
    print("Connecting to local Ollama server...")
    client = OpenAI(
        base_url='http://localhost:11434/v1', 
        api_key='ollama'
    )
    client.models.list() 
    print(f"Successfully connected to Ollama. Using model: {OLLAMA_MODEL_NAME}")
    
except Exception as e:
    print("!!! FAILED TO CONNECT TO OLLAMA !!!")
    raise RuntimeError(f"Failed to connect to Ollama: {e}")


# --- 2. Load "Memory" (FAISS) ---
def load_memory():
    """Loads FAISS index and notes. Returns (index, notes)"""
    print("Loading memory (FAISS index and notes)...")
    try:
        # Create data dir if it doesn't exist
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        if not os.path.exists("my_faiss.index") or not os.path.exists("my_notes.json"):
            print("WARNING: Memory files not found. Attempting to build index...")
            build_index(DATA_DIR)
            
        index = faiss.read_index("my_faiss.index")
        with open('my_notes.json', 'r', encoding='utf-8') as f:
            notes = json.load(f)
        print(f"Memory loaded. {len(notes)} notes indexed.")
        return index, notes
    except Exception as e:
        print(f"Error loading memory: {e}")
        return None, []

index, notes = load_memory()

# --- 3. Setup Flask API ---
app = Flask(__name__)
CORS(app) 

# (search_in_memory and get_query_intent functions remain unchanged)
def search_in_memory(query, k=3):
    if not index or not notes: return []
    k = min(k, len(notes))
    if k == 0: return []
    query_vector = embed_model.encode([query], normalize_embeddings=True)
    distances, indices = index.search(query_vector, k)
    return [notes[i] for i in indices[0]]

def get_query_intent(user_prompt):
    print(f"Routing query: '{user_prompt}'")
    try:
        router_prompt = "Analyze the user query: '{user_prompt}'. Is this simple chit-chat, or a specific question requiring a knowledge base search? Answer with only 'CHITCHAT' or 'SEARCH'."
        response = client.chat.completions.create(model=OLLAMA_MODEL_NAME, messages=[{"role": "user", "content": router_prompt.format(user_prompt=user_prompt)}], temperature=0.0)
        intent = response.choices[0].message.content.strip().upper()
        if "SEARCH" in intent:
            print("Router decision: SEARCH")
            return "SEARCH"
        else:
            print("Router decision: CHITCHAT")
            return "CHITCHAT"
    except Exception as e:
        print(f"Error in query router: {e}. Defaulting to 'SEARCH'.")
        return "SEARCH"

# --- Endpoint 1: Chat (Unchanged Persona) ---
@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    messages_from_user = data.get('messages')
    if not messages_from_user: return jsonify({"error": "Field 'messages' is required"}), 400

    try:
        current_prompt = messages_from_user[-1]['content']
        intent = get_query_intent(current_prompt)
        context_str = "No relevant internal documents found."
        found_context_data = []

        if intent == "SEARCH":
            context_notes = search_in_memory(current_prompt)
            if context_notes:
                print(f"Found {len(context_notes)} relevant notes.")
                context_for_prompt = [note['content'] for note in context_notes]
                found_context_data = [note for note in context_notes] 
                context_str = "\n---\n".join(context_for_prompt)
            else:
                print("No relevant context found.")
        else:
            print("Skipping memory search for CHITCHAT.")
            context_str = "Context not needed for this query."

        system_message = {
            "role": "system",
            "content": f"You are 'CoreMind', a personalized AI assistant. Answer questions based on the provided context. If the answer isn't in the context, say so. If it's chit-chat, be polite.\n--- CONTEXT: {context_str} ---"
        }
        final_messages = [system_message] + messages_from_user
        response = client.chat.completions.create(model=OLLAMA_MODEL_NAME, messages=final_messages)
        response_text = response.choices[0].message.content
        return jsonify({"response_text": response_text, "found_context": found_context_data})

    except Exception as e:
        print(f"Error during query: {e}")
        return jsonify({"error": str(e)}), 500

# --- Endpoint 2: Add Note (Instant Rebuild) ---
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
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Note saved to {filename}. Rebuilding entire index...")
        success, message = build_index(DATA_DIR)
        if not success:
            return jsonify({"error": f"Note saved, but index rebuild failed: {message}"}), 500
        
        index, notes = load_memory()
        print("Memory successfully reloaded.")
        return jsonify({"success": True, "message": f"Note saved and memory updated. Total notes: {len(notes)}"}), 201
    except Exception as e:
        print(f"Error saving note or rebuilding: {e}")
        return jsonify({"error": str(e)}), 500

# --- NEW Endpoint 3: Upload File ---
@app.route('/upload_file', methods=['POST'])
def upload_file():
    global index, notes 
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        try:
            # Secure the filename and save it to the data directory
            filename = secure_filename(file.filename)
            filepath = os.path.join(DATA_DIR, filename)
            file.save(filepath)
            
            # Now that the file is saved, rebuild the entire index
            print(f"File saved to {filename}. Rebuilding entire index...")
            success, message = build_index(DATA_DIR)
            
            if not success:
                return jsonify({"error": f"File saved, but index rebuild failed: {message}"}), 500
            
            # Reload the memory in real-time
            index, notes = load_memory()
            print("Memory successfully reloaded.")
            return jsonify({"success": True, "message": f"File '{filename}' uploaded and memory updated. Total items: {len(notes)}"}), 201
            
        except Exception as e:
            print(f"Error uploading file: {e}")
            return jsonify({"error": str(e)}), 500

# --- Run Server ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI 

# Import our memory utilities
from memory_utils import build_index, load_embedding_model

print("Starting CoreMind API (v0.5 - Instant Memory)...")

# --- 1. Load Config and Models ---
load_dotenv()

OLLAMA_MODEL_NAME = "llama3.1:8b" 

try:
    print("Loading embedding model (for FAISS)...")
    embed_model = load_embedding_model() # from memory_utils
    
    print("Connecting to local Ollama server...")
    client = OpenAI(
        base_url='http://localhost:11434/v1', # Ollama's default address
        api_key='ollama' # 'ollama' is the default key
    )
    
    client.models.list() 
    print(f"Successfully connected to Ollama. Using model: {OLLAMA_MODEL_NAME}")
    
except Exception as e:
    print("!!! FAILED TO CONNECT TO OLLAMA !!!")
    print("Is Ollama running? Did you run 'ollama run llama3.1:8b'?")
    raise RuntimeError(f"Failed to connect to Ollama: {e}")


# --- 2. Load "Memory" (FAISS) ---
def load_memory():
    """Loads FAISS index and notes. Returns (index, notes)"""
    print("Loading memory (FAISS index and notes)...")
    try:
        if not os.path.exists("my_faiss.index") or not os.path.exists("my_notes.json"):
            print("WARNING: Memory files not found. Index is empty.")
            # Let's run build_index() to create them if they're missing
            print("Attempting to build index from /data folder...")
            build_index("./data/")
            
        index = faiss.read_index("my_faiss.index")
        with open('my_notes.json', 'r', encoding='utf-8') as f:
            notes = json.load(f)
        print(f"Memory loaded. {len(notes)} notes indexed.")
        return index, notes
    except Exception as e:
        print(f"Error loading memory: {e}")
        return None, []

index, notes = load_memory()

# --- 3. Setup Flask API ---
app = Flask(__name__)
CORS(app) 

def search_in_memory(query, k=3):
    """Internal search function"""
    if not index or not notes:
        print("Search skipped: Memory is empty.")
        return []
    k = min(k, len(notes))
    if k == 0:
        return []
    query_vector = embed_model.encode([query], normalize_embeddings=True)
    distances, indices = index.search(query_vector, k)
    results = [notes[i] for i in indices[0]]
    return results

# --- Query Router Function ---
def get_query_intent(user_prompt):
    """
    Analyzes the user's prompt to decide if it's simple chit-chat
    or a specific question that requires a memory search.
    """
    print(f"Routing query: '{user_prompt}'")
    try:
        router_prompt = f"""
        Analyze the user query: '{user_prompt}'
        Is this a simple greeting, thank you, or general small talk? 
        Or is it a specific question that likely requires searching a knowledge base?
        
        Answer with only one word: 'CHITCHAT' or 'SEARCH'.
        """
        
        response = client.chat.completions.create(
            model=OLLAMA_MODEL_NAME,
            messages=[{"role": "user", "content": router_prompt}],
            temperature=0.0
        )
        intent = response.choices[0].message.content.strip().upper()
        
        if "SEARCH" in intent:
            print("Router decision: SEARCH")
            return "SEARCH"
        else:
            print("Router decision: CHITCHAT")
            return "CHITCHAT"
            
    except Exception as e:
        print(f"Error in query router: {e}. Defaulting to 'SEARCH'.")
        return "SEARCH"

# --- Endpoint 1: Chat (Updated Persona) ---
@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    messages_from_user = data.get('messages')

    if not messages_from_user:
        return jsonify({"error": "Field 'messages' is required"}), 400

    try:
        current_prompt = messages_from_user[-1]['content']
        intent = get_query_intent(current_prompt)
        
        context_str = "No relevant internal documents found."
        found_context_data = []

        if intent == "SEARCH":
            context_notes = search_in_memory(current_prompt)
            if context_notes:
                print(f"Found {len(context_notes)} relevant notes.")
                context_for_prompt = [note['content'] for note in context_notes]
                found_context_data = [note for note in context_notes] 
                context_str = "\n---\n".join(context_for_prompt)
            else:
                print("No relevant context found.")
        else:
            print("Skipping memory search for CHITCHAT.")
            context_str = "Context not needed for this query."

        # --- NEW STRICTER PERSONA (v0.7) ---
        system_message = {
            "role": "system",
            "content": f"""
            You are 'CoreMind', a specialized AI assistant. Your ONLY task is to answer user questions based *exclusively* on the provided context.
            
            ---
            CONTEXT FROM KNOWLEDGE BASE:
            {context_str}
            ---

            Follow these rules strictly:
            1.  Analyze the user's last question.
            2.  Find the answer ONLY within the 'CONTEXT FROM KNOWLEDGE BASE' provided above.
            3.  If the answer IS in the context, synthesize it and provide a clear, helpful response.
            4.  If the answer IS NOT in the context (or if the context says "No relevant documents found"), you MUST respond with: "I'm sorry, I don't have that specific information in my knowledge base."
            5.  DO NOT, under any circumstances, mention your internal workings (e.g., "I cannot access files", "I am an AI"). Just answer based on the context or say you don't have the information.
            6.  If the user is making small talk (like 'hello', 'thanks'), respond politely as an AI assistant.
            """
        }
        # --- END OF NEW PROMPT ---
        
        final_messages = [system_message] + messages_from_user

        response = client.chat.completions.create(
            model=OLLAMA_MODEL_NAME,
            messages=final_messages
        )
        
        response_text = response.choices[0].message.content
        
        return jsonify({
            "response_text": response_text,
            "found_context": found_context_data
        })

    except Exception as e:
        print(f"Error during query: {e}")
        return jsonify({"error": str(e)}), 500

# --- Endpoint 2: Add Note (NEW LOGIC) ---
@app.route('/add_note', methods=['POST'])
def add_note():
    global index, notes # We will be modifying the global memory
    data = request.json
    content = data.get('content')
    
    if not content or not content.strip():
        return jsonify({"error": "Note content cannot be empty"}), 400
        
    try:
        # 1. Save the file (for persistence)
        data_dir = "./data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        timestamp = int(time.time())
        filename = f"note_{timestamp}.txt"
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # 2. Rebuild the ENTIRE index (this is the new logic)
        print(f"Note saved to {filename}. Rebuilding entire index...")
        success, message = build_index(data_dir)
        
        if not success:
            # If build fails, return error
            print(f"Failed to rebuild index: {message}")
            return jsonify({"error": f"Note was saved, but index rebuild failed: {message}"}), 500

        # 3. Reload the global memory variables
        index, notes = load_memory()
        print("Memory successfully reloaded.")
            
        return jsonify({
            "success": True, 
            "message": f"Note saved and memory updated. Total notes: {len(notes)}"
        }), 201

    except Exception as e:
        print(f"Error saving note or rebuilding: {e}")
        return jsonify({"error": str(e)}), 500

# --- Endpoint 3: Rebuild Index (REMOVED) ---
# We removed this endpoint as '/add_note' now handles rebuilding.
# We will keep the 'build_index' function in memory_utils.py.


# --- Run Server ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)