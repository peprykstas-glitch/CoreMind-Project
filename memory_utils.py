import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import os
import glob
import json
import streamlit as st
import pypdf         # Import for PDF
import docx          # Import for DOCX

# We define the embedding model as a constant
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

@st.cache_resource
def load_embedding_model():
    # Loads the embedding model (cached by Streamlit)
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    return SentenceTransformer(EMBEDDING_MODEL)

# --- NEW: Function to extract text from different files ---
def extract_text_from_file(file_path):
    """Extracts raw text from .txt, .md, .pdf, and .docx files."""
    print(f"Extracting text from: {file_path}")
    if file_path.endswith(".pdf"):
        try:
            reader = pypdf.PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
            return None
            
    elif file_path.endswith(".docx"):
        try:
            doc = docx.Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            print(f"Error reading DOCX {file_path}: {e}")
            return None
            
    elif file_path.endswith(".txt") or file_path.endswith(".md"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return None
    else:
        print(f"Skipping unsupported file type: {file_path}")
        return None

def build_index(data_directory="./data/"):
    """
    Reads all supported files (.txt, .md, .pdf, .docx) from data_directory, 
    creates embeddings, and saves the FAISS index and notes.
    """
    try:
        model = load_embedding_model()
        my_notes = []
        
        # Glob for all supported file types
        file_paths = glob.glob(os.path.join(data_directory, "*.txt"))
        file_paths.extend(glob.glob(os.path.join(data_directory, "*.md")))
        file_paths.extend(glob.glob(os.path.join(data_directory, "*.pdf")))
        file_paths.extend(glob.glob(os.path.join(data_directory, "*.docx")))

        if not file_paths:
            return (False, f"No supported files (.txt, .md, .pdf, .docx) found in {data_directory} folder.")

        print(f"Reading {len(file_paths)} files from {data_directory}...")
        for file_path in file_paths:
            # Use our new function to get text
            content = extract_text_from_file(file_path)
            
            if content and content.strip(): # Only add non-empty files
                note = {
                    "source": os.path.basename(file_path),
                    "content": content
                }
                my_notes.append(note)
            else:
                print(f"Skipping empty or unreadable file: {file_path}")
        
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
            
        return (True, f"Memory successfully updated. Processed {len(my_notes)} files.")
    
    except Exception as e:
        print(f"An error occurred in build_index: {e}")
        return (False, f"An error occurred: {e}")