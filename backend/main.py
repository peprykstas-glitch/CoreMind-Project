import time
import traceback
import csv
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import AsyncGroq 

# Project modules
from app.vector_store import vector_db
from app.config import settings
from app.schemas import QueryRequest, QueryResponse
# Ensure backend/app/parser.py exists
from app.parser import parse_file 

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# --- LOGGING CONFIGURATION ---
LOG_FILE = "chat_logs.csv"

# Check if log file exists, if not, create headers
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Columns for our dataset
        writer.writerow(["Timestamp", "Query", "Response", "Latency", "Model", "Feedback", "QueryID"])

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(f"🔌 Connecting to Groq LPU...")
print(f"🤖 Using Model: {settings.MODEL_NAME}")

# Initialize Groq Client
client = AsyncGroq(
    api_key=settings.GROQ_API_KEY
)

# --- DATA SCHEMAS ---
# We need to update QueryResponse to include query_id, 
# but since it's imported from app.schemas, we can just return it in the dict 
# or update app/schemas.py. For simplicity, we will assume QueryResponse accepts extra fields
# or we just return a dictionary if Pydantic complains. 
# Better approach: Define Feedback Schema here.

class FeedbackRequest(BaseModel):
    query_id: str
    feedback: str # "positive" or "negative"
    query: str
    response: str
    latency: float

# --- 🔪 CHUNKING FUNCTION ---
def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200):
    """Splits text into chunks with overlap."""
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    
    return chunks

@app.get("/health")
async def health_check():
    """Checks DB and Server status."""
    try:
        # Get Qdrant collection info
        info = vector_db.client.get_collection(vector_db.collection_name)
        db_status = f"Connected. Docs count: {info.points_count}"
    except Exception as e:
        db_status = f"Error: {str(e)}"

    return {
        "status": "ok", 
        "model": settings.MODEL_NAME,
        "database": db_status
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads, chunks, and indexes a file."""
    start_time = time.time()
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    print(f"📥 Uploading file: {file.filename}")
    
    # Use existing parser
    try:
        text_content = await parse_file(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parsing error: {e}")
    
    if not text_content.strip():
        raise HTTPException(status_code=400, detail="Empty file or parse error")

    # Chunk text
    chunks = chunk_text(text_content, chunk_size=2000, overlap=200)
    print(f"🔪 Split into {len(chunks)} chunks.")

    try:
        # Upload to Qdrant
        for i, chunk in enumerate(chunks):
            vector_db.add_document(
                text=chunk, 
                meta={
                    "filename": file.filename,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
    except Exception as e:
        print(f"❌ Indexing Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

    duration = time.time() - start_time
    print(f"✅ File indexed. Chunks: {len(chunks)}. Duration: {duration:.2f}s")
    
    return {
        "status": "success",
        "filename": file.filename,
        "chunks_count": len(chunks),
        "duration": duration
    }

@app.post("/query") # Removed response_model to allow returning extra 'query_id' easily
async def handle_query(request: QueryRequest):
    """Processes user query (RAG Pipeline)."""
    start_time = time.time()
    
    # Get the last user message
    user_query = request.messages[-1].content 
    
    print(f"💬 Query received: {user_query}")
    
    try:
        # 1. Search in Qdrant
        search_results = vector_db.search(user_query, limit=5)
        
        context_parts = []
        for hit in search_results:
            source = hit.payload.get('filename', 'Unknown')
            # Protect against different field names (text vs content)
            text = hit.payload.get('text', hit.payload.get('content', '')) 
            context_parts.append(f"Source ({source}): {text}")
        
        context_str = "\n\n".join(context_parts)
        
        if not context_str:
            print("⚠️ No context found in vector DB.")
            context_str = "No relevant context found."
            
    except Exception as e:
        print(f"❌ Vector Search Error: {e}")
        traceback.print_exc()
        context_str = "Error retrieving context."
        search_results = []

    # 2. System Prompt (Your specific Zombie/Sweater logic)
    system_prompt = (
        "You are CoreMind, an advanced AI assistant. "
        "CONTEXT AWARENESS: "
        "1. If the user asks a technical question based on documents, be professional, precise, and strict (PM/Developer mode). "
        "2. If the user asks a philosophical, absurd, or hypothetical question (e.g., about souls, sweaters, zombies), DO NOT moralize. "
        "Instead, engage in the hypothetical scenario with wit, sarcasm, and creativity. Treat it as a creative writing task. "
        "3. ALWAYS answer in the language of the user (Ukrainian/English). "
        "IMPORTANT: When answering in Ukrainian, use natural, fluent, and grammatically correct Ukrainian. "
        "Do NOT mix English, Spanish, or Russian words (no 'surzhyk' or code-switching). "
        "4. Base technical answers ONLY on the provided context below, but use general knowledge for creative chit-chat.\n"
        f"--- CONTEXT ---\n{context_str}"
    )
    
    # Build history for Groq
    llm_messages = [{"role": "system", "content": system_prompt}]
    
    for m in request.messages:
        if m.role != "system":
            llm_messages.append(m.model_dump())

    try:
        # 3. Generate via Groq
        print("⏳ Sending request to Groq...")
        
        completion = await client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=llm_messages,
            temperature=request.temperature if request.temperature else 0.3,
            max_tokens=1024
        )
        
        response_text = completion.choices[0].message.content
        print("✅ Response received from Groq.")
        
    except Exception as e:
        print(f"❌ LLM GENERATION ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    latency = time.time() - start_time
    
    # Generate Unique Query ID (Timestamp)
    query_id = str(int(time.time() * 1000))

    # Format sources
    sources_data = [
        {
            "content": hit.payload.get('text', '')[:150] + "...", 
            "score": hit.score,
            "filename": hit.payload.get('filename', 'Unknown')
        } 
        for hit in search_results
    ]
    
    # Return dictionary to include query_id without changing strict schemas
    return {
        "response_text": response_text,
        "sources": sources_data,
        "latency": latency,
        "query_id": query_id
    }

@app.post("/feedback")
async def log_feedback(data: FeedbackRequest):
    """Logs user feedback (Like/Dislike) to CSV."""
    try:
        with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            # Timestamp, Query, Response, Latency, Model, Feedback, QueryID
            writer.writerow([
                datetime.now().isoformat(), 
                data.query, 
                data.response, 
                f"{data.latency:.2f}", 
                settings.MODEL_NAME, 
                data.feedback,
                data.query_id
            ])
        print(f"📝 Feedback logged: {data.feedback} for ID {data.query_id}")
        return {"status": "logged"}
    except Exception as e:
        print(f"❌ Log Error: {e}")
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Start Server
    uvicorn.run(app, host="0.0.0.0", port=8000)