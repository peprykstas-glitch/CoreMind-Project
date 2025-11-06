import os
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI # Новий імпорт!

# Імпортуємо наші утиліти для пам'яті
from memory_utils import build_index, load_embedding_model

print("Starting CoreMind API (v0.4 - Router Edition)...")

# --- 1. Load Config and Models ---
load_dotenv()

OLLAMA_MODEL_NAME = "llama3.1:8b" 

try:
    print("Loading embedding model (for FAISS)...")
    embed_model = load_embedding_model() # з memory_utils
    
    print("Connecting to local Ollama server...")
    # Це "телефон" до вашої локальної "плити" Ollama
    client = OpenAI(
        base_url='http://localhost:11434/v1', # Стандартна адреса Ollama
        api_key='ollama' # Ключ не потрібен, але бібліотека вимагає
    )
    
    # Перевірка з'єднання (спробуємо отримати список моделей)
    client.models.list() 
    print(f"Successfully connected to Ollama. Using model: {OLLAMA_MODEL_NAME}")
    
except Exception as e:
    print("!!! FAILED TO CONNECT TO OLLAMA !!!")
    print("Is Ollama running? Did you run 'ollama run llama3.1:8b'?")
    raise RuntimeError(f"Failed to connect to Ollama: {e}")


# --- 2. Load "Memory" (FAISS) ---
def load_memory():
    """Завантажує індекс FAISS та нотатки. Повертає (index, notes)"""
    print("Loading memory (FAISS index and notes)...")
    try:
        if not os.path.exists("my_faiss.index") or not os.path.exists("my_notes.json"):
            print("WARNING: Memory files not found. Index is empty.")
            return None, [] 
            
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
    """Внутрішня функція пошуку (без змін)"""
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

# --- NEW FUNCTION: Query Router ---
def get_query_intent(user_prompt):
    """
    Analyzes the user's prompt to decide if it's simple chit-chat
    or a specific question that requires a memory search.
    """
    print(f"Routing query: '{user_prompt}'")
    try:
        router_prompt = f"""
        Analyze the following user query: '{user_prompt}'
        Is this a simple greeting, a thank you, or general small talk? 
        Or is it a specific question that likely requires searching a knowledge base (about hotels, students, documents, procedures, etc.)?
        
        Answer with only one word: 'CHITCHAT' or 'SEARCH'.
        """
        
        response = client.chat.completions.create(
            model=OLLAMA_MODEL_NAME,
            messages=[{"role": "user", "content": router_prompt}],
            temperature=0.0 # Робимо його дуже точним
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
        return "SEARCH" # Якщо щось пішло не так, краще шукати

# --- Endpoint 1: Chat (ОНОВЛЕНО з Роутером) ---
@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    messages_from_user = data.get('messages') # Історія чату від app.py

    if not messages_from_user:
        return jsonify({"error": "Field 'messages' is required"}), 400

    try:
        current_prompt = messages_from_user[-1]['content']
        
        # === КРОК 1: ВИКОРИСТОВУЄМО РОУТЕР ===
        intent = get_query_intent(current_prompt)
        
        context_str = "No relevant internal documents found."
        found_context_data = []

        # === КРОК 2: ШУКАЄМО, ТІЛЬКИ ЯКЩО ПОТРІБНО ===
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
            # Якщо це 'CHITCHAT', ми не шукаємо в пам'яті.
            print("Skipping memory search for CHITCHAT.")
            context_str = "Context not needed for this query."


        # === КРОК 3: БУДУЄМО ПРОМПТ ===
        system_message = {
            "role": "system",
            "content": f"""
            You are 'Ana', an expert AI assistant for project manager. 
            You MUST use the internal knowledge base (context) provided below to answer.
            If the answer isn't in the context, say "I don't have that information in my knowledge base."
            If the query is simple chit-chat (like 'hello' or 'thank you'), just be polite and helpful.
            ---
            CONTEXT FROM KNOWLEDGE BASE:
            {context_str}
            ---
            """
        }
        
        final_messages = [system_message] + messages_from_user

        # === КРОК 4: ГЕНЕРУЄМО ВІДПОВІДЬ ===
        response = client.chat.completions.create(
            model=OLLAMA_MODEL_NAME,
            messages=final_messages
        )
        
        response_text = response.choices[0].message.content
        
        return jsonify({
            "response_text": response_text,
            "found_context": found_context_data # Все ще повертаємо це, щоб `app.py` міг це показати
        })

    except Exception as e:
        print(f"Error during query: {e}")
        return jsonify({"error": str(e)}), 500

# --- Ендпоінт 2: Add Note (Без змін) ---
@app.route('/add_note', methods=['POST'])
def add_note():
    # ... (цей код не змінився) ...
    data = request.json
    content = data.get('content')
    if not content or not content.strip():
        return jsonify({"error": "Note content cannot be empty"}), 400
    try:
        data_dir = "./data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        timestamp = int(time.time())
        filename = f"note_{timestamp}.txt"
        filepath = os.path.join(data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({
            "success": True, 
            "message": f"Note saved to {filename}. Please rebuild index to use it."
        }), 201
    except Exception as e:
        print(f"Error saving note: {e}")
        return jsonify({"error": str(e)}), 500


# --- Ендпоінт 3: Rebuild Index (Без змін) ---
@app.route('/rebuild_index', methods=['POST'])
def rebuild_memory_index():
    # ... (цей код не змінився) ...
    global index, notes 
    print("Rebuilding memory index...")
    try:
        success, message = build_index("./data/")
        if success:
            index, notes = load_memory()
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 500
    except Exception as e:
        print(f"Error rebuilding index: {e}")
        return jsonify({"error": str(e)}), 500


# --- Run Server ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)