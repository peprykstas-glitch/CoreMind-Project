import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import os
import glob
import json
import streamlit as st

EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

@st.cache_resource
def load_embedding_model():
    """Loads the embedding model (cached)"""
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    return SentenceTransformer(EMBEDDING_MODEL)

def build_index(data_directory="./data/"):
    """
    Reads files from data_directory, creates embeddings, and saves 
    the FAISS index (my_faiss.index) and notes (my_notes.json).
    Returns (True, "Success message") or (False, "Error message").
    """
    try:
        model = load_embedding_model()
        
        my_notes = []
        file_paths = glob.glob(os.path.join(data_directory, "*.txt"))
        file_paths.extend(glob.glob(os.path.join(data_directory, "*.md")))

        if not file_paths:
            return (False, f"No .txt or .md files found in {data_directory} folder.")

        print(f"Reading {len(file_paths)} files from {data_directory}...")
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip(): 
                        note = {
                            "source": os.path.basename(file_path),
                            "content": content
                        }
                        my_notes.append(note)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        if not my_notes:
            return (False, "Files were found, but they are empty or could not be read.")

        print(f"Creating embeddings for {len(my_notes)} notes...")
        note_contents = [note['content'] for note in my_notes]
        embeddings = model.encode(note_contents, normalize_embeddings=True)
        
        d = embeddings.shape[1]
        
        print("Building FAISS index...")
        index = faiss.IndexFlatL2(d)
        index = faiss.IndexIDMap(index) 
        index.add_with_ids(embeddings, np.arange(len(my_notes)))

        print("Saving index (my_faiss.index) and notes (my_notes.json)...")
        faiss.write_index(index, "my_faiss.index")
        
        with open('my_notes.json', 'w', encoding='utf-8') as f:
            json.dump(my_notes, f, ensure_ascii=False, indent=4)
            
        return (True, f"Memory successfully updated. Processed {len(my_notes)} notes.")
    
    except Exception as e:
        print(f"An error occurred in build_index: {e}")
        return (False, f"An error occurred: {e}")