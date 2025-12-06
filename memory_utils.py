import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import os
import glob
import json
import streamlit as st
import pypdf
import docx
from typing import Tuple, List, Optional, Any

# Constants
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
INDEX_FILE = "my_faiss.index"
NOTES_FILE = "my_notes.json"

@st.cache_resource
def load_embedding_model() -> SentenceTransformer:
    """
    Loads the embedding model. Cached by Streamlit to avoid reloading on every run.
    """
    print(f"Loading embedding model ({EMBEDDING_MODEL_NAME})...")
    return SentenceTransformer(EMBEDDING_MODEL_NAME)

def extract_text_from_file(file_path: str) -> Optional[str]:
    """
    Extracts raw text from .txt, .md, .pdf, and .docx files.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        Optional[str]: Extracted text or None if failed.
    """
    print(f"Extracting text from: {file_path}")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None

    try:
        if file_path.endswith(".pdf"):
            reader = pypdf.PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
            
        elif file_path.endswith(".docx"):
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
            
        elif file_path.endswith((".txt", ".md")):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        else:
            print(f"Skipping unsupported file type: {file_path}")
            return None
            
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def save_memory_state(index: Any, notes: List[dict]) -> None:
    """Helper function to save index and notes to disk."""
    print("Saving index and notes to disk...")
    faiss.write_index(index, INDEX_FILE)
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=4)

def add_document_to_index(file_path: str, index: Any, notes: List[dict]) -> Tuple[bool, str, Any, List[dict]]:
    """
    INCREMENTAL INDEXING: Adds a single document to the existing FAISS index and notes list.
    
    Returns:
        Tuple: (Success boolean, Message string, Updated Index, Updated Notes)
    """
    try:
        model = load_embedding_model()
        content = extract_text_from_file(file_path)
        
        if not content or not content.strip():
            return False, "File is empty or unreadable.", index, notes

        # Create new note object
        new_note = {
            "source": os.path.basename(file_path),
            "content": content
        }
        
        # Create embedding for the SINGLE new note
        # encode expects a list, so we wrap content in []
        new_embedding = model.encode([content], normalize_embeddings=True)
        
        # Add to FAISS index
        # We need to calculate the new ID (which is just the current length of notes)
        current_id = len(notes)
        index.add_with_ids(new_embedding, np.array([current_id]).astype('int64'))
        
        # Add to notes list
        notes.append(new_note)
        
        # Save state
        save_memory_state(index, notes)
        
        return True, f"Successfully added '{os.path.basename(file_path)}' to memory.", index, notes

    except Exception as e:
        print(f"Error in incremental update: {e}")
        return False, f"Error updating memory: {str(e)}", index, notes

def build_index_from_scratch(data_directory: str = "./data/") -> Tuple[bool, str]:
    """
    FULL REBUILD: Reads all files and rebuilds the index from scratch.
    Useful for initialization or hard resets.
    """
    try:
        model = load_embedding_model()
        my_notes = []
        
        # Glob for all supported file types
        extensions = ["*.txt", "*.md", "*.pdf", "*.docx"]
        file_paths = []
        for ext in extensions:
            file_paths.extend(glob.glob(os.path.join(data_directory, ext)))

        if not file_paths:
            return False, f"No supported files found in {data_directory} folder."

        print(f"Full rebuild: Reading {len(file_paths)} files...")
        
        valid_contents = []
        
        for file_path in file_paths:
            content = extract_text_from_file(file_path)
            if content and content.strip():
                my_notes.append({
                    "source": os.path.basename(file_path),
                    "content": content
                })
                valid_contents.append(content)
            else:
                print(f"Skipping empty: {file_path}")
        
        if not my_notes:
            return False, "Files found but empty/unreadable."

        print(f"Creating embeddings for {len(my_notes)} notes...")
        embeddings = model.encode(valid_contents, normalize_embeddings=True)
        
        d = embeddings.shape[1] 
        index = faiss.IndexFlatL2(d)
        index = faiss.IndexIDMap(index) 
        index.add_with_ids(embeddings, np.arange(len(my_notes)))

        save_memory_state(index, my_notes)
            
        return True, f"Memory fully rebuilt. Indexed {len(my_notes)} documents."
    
    except Exception as e:
        print(f"Critical error in build_index: {e}")
        return False, f"An error occurred: {e}"