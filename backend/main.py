import time
import traceback
import csv
import os
from datetime import datetime
import pandas as pd  # <--- Make sure to run: pip install pandas
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import AsyncGroq
from qdrant_client.http import models # Required for filtering deletion

# Project modules
from app.vector_store import vector_db
from app.config import settings
from app.schemas import QueryRequest
from app.parser import parse_file 

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# --- LOGGING CONFIGURATION ---
LOG_FILE = "chat_logs.csv"

# Initialize CSV with headers if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Query", "Response", "Latency", "Model", "Feedback", "QueryID"])

# --- CORS CONFIGURATION ---
# Allows frontend (Next.js) to communicate with backend
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
client = AsyncGroq(api_key=settings.GROQ_API_KEY)

# --- DATA SCHEMAS ---
class FeedbackRequest(BaseModel):
    query_id: str
    feedback: str # "positive" or "negative"
    query: str
    response: str
    latency: float

class DeleteFileRequest(BaseModel):
    filename: str

# --- UTILS ---
def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200):
    """Splits text into chunks with overlap for better context retention."""
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    
    return chunks

# --- ENDPOINTS ---

@app.get("/health")
async def health_check():
    """Checks DB connection and Server status."""
    try:
        info = vector_db.client.get_collection(vector_db.collection_name)
        db_status = f"Connected. Docs count: {info.points_count}"
    except Exception as e:
        db_status = f"Error: {str(e)}"

    return {
        "status": "ok", 
        "model": settings.MODEL_NAME,
        "database": db_status
    }

@app.get("/analytics")
async def get_analytics():
    """
    Reads logs from CSV and calculates KPIs for the Dashboard.
    Returns: Total queries, Avg Latency, Likes/Dislikes, and Historical Data.
    """
    if not os.path.exists(LOG_FILE):
        return {"total": 0, "avg_latency": 0, "likes": 0, "dislikes": 0, "history": [], "models": {}}
    
    try:
        df = pd.read_csv(LOG_FILE)
        if df.empty:
            return {"total": 0, "avg_latency": 0, "likes": 0, "dislikes": 0, "history": [], "models": {}}

        # Calculate KPIs
        total = len(df)
        # Check if 'Latency' exists and is numeric
        avg_lat = df["Latency"].mean() if "Latency" in df and pd.to_numeric(df["Latency"], errors='coerce').notnull().all() else 0
        
        likes = len(df[df["Feedback"] == "positive"]) if "Feedback" in df else 0
        dislikes = len(df[df["Feedback"] == "negative"]) if "Feedback" in df else 0
        
        # Data for Charts (Last 50 records)
        history = []
        if "Timestamp" in df and "Latency" in df:
            history = df[["Timestamp", "Latency"]].tail(50).fillna(0).to_dict(orient="records")
        
        models_stats = df["Model"].value_counts().to_dict() if "Model" in df else {}

        return {
            "total": total,
            "avg_latency": round(float(avg_lat), 2),
            "likes": likes,
            "dislikes": dislikes,
            "history": history,
            "models": models_stats
        }
    except Exception as e:
        print(f"❌ Analytics Error: {e}")
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads, parses, chunks, and indexes a file."""
    start_time = time.time()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    print(f"📥 Uploading file: {file.filename}")
    
    # Parse file content
    try:
        text_content = await parse_file(file)
    except Exception as e:
        print(f"❌ Parsing Error: {e}")
        raise HTTPException(status_code=400, detail=f"Parsing error: {str(e)}")
    
    if not text_content or not text_content.strip():
        raise HTTPException(status_code=400, detail="Empty file or content cannot be parsed")

    # Chunk text
    chunks = chunk_text(text_content, chunk_size=2000, overlap=200)
    print(f"🔪 Split into {len(chunks)} chunks.")

    # Index into Qdrant
    try:
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
    print(f"✅ File indexed. Duration: {duration:.2f}s")
    
    return {
        "status": "success",
        "filename": file.filename,
        "chunks_count": len(chunks),
        "duration": duration
    }

@app.get("/files")
async def list_files():
    """Returns a list of all unique filenames currently in the database."""
    try:
        unique_files = set()
        next_offset = None
        
        while True:
            res = vector_db.client.scroll(
                collection_name=vector_db.collection_name,
                limit=2000,  
                with_payload=True,
                with_vectors=False,
                offset=next_offset
            )
            points, next_offset = res
            
            for point in points:
                if point.payload and "filename" in point.payload:
                    unique_files.add(point.payload["filename"])
            
            if next_offset is None:
                break
        
        return {"files": list(unique_files)}
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return {"files": [], "error": str(e)}

@app.post("/delete_file")
async def delete_file(request: DeleteFileRequest):
    """Deletes all vectors associated with a specific filename."""
    try:
        vector_db.client.delete(
            collection_name=vector_db.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="filename",
                            match=models.MatchValue(value=request.filename),
                        ),
                    ],
                )
            ),
        )
        print(f"🗑️ Deleted file: {request.filename}")
        return {"status": "deleted", "filename": request.filename}
    except Exception as e:
        print(f"❌ Delete Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def handle_query(request: QueryRequest):
    """Core RAG Pipeline: Search -> Prompt -> Generate."""
    start_time = time.time()
    user_query = request.messages[-1].content 
    print(f"💬 Query received: {user_query}")
    
    # 1. Search Vector DB
    try:
        search_results = vector_db.search(user_query, limit=5)
        context_parts = []
        for hit in search_results:
            source = hit.payload.get('filename', 'Unknown')
            text = hit.payload.get('text', hit.payload.get('content', '')) 
            context_parts.append(f"Source ({source}): {text}")
        
        context_str = "\n\n".join(context_parts) if context_parts else "No relevant context found."
            
    except Exception as e:
        print(f"❌ Search Error: {e}")
        context_str = "Error retrieving context."
        search_results = []

    # 2. Construct System Prompt
    system_prompt = (
        "You are Vectrieve, an advanced AI assistant. "
        "INSTRUCTIONS:\n"
        "1. Answer strictly based on the CONTEXT provided below. If the answer is not in the context, say so.\n"
        "2. Be concise, professional, and technical.\n"
        "3. If the user asks general questions (non-technical), be witty and creative.\n"
        f"--- CONTEXT ---\n{context_str}"
    )
    
    # 3. Prepare Messages for LLM
    llm_messages = [{"role": "system", "content": system_prompt}]
    for m in request.messages:
        if m.role != "system":
            llm_messages.append(m.model_dump())

    # 4. Generate Response
    try:
        temp = request.temperature if request.temperature is not None else 0.3
        completion = await client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=llm_messages,
            temperature=temp,
            max_tokens=1024
        )
        response_text = completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    latency = time.time() - start_time
    query_id = str(int(time.time() * 1000))

    # 5. Format Sources for Frontend
    sources_data = [
        {
            "content": hit.payload.get('text', '')[:150] + "...", 
            "score": hit.score,
            "filename": hit.payload.get('filename', 'Unknown')
        } 
        for hit in search_results
    ]
    
    return {
        "response_text": response_text,
        "sources": sources_data,
        "latency": latency,
        "query_id": query_id
    }

@app.post("/feedback")
async def log_feedback(data: FeedbackRequest):
    """Logs user feedback to CSV for analysis."""
    try:
        with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                datetime.now().isoformat(), 
                data.query, 
                data.response, 
                f"{data.latency:.2f}", 
                settings.MODEL_NAME, 
                data.feedback,
                data.query_id
            ])
        return {"status": "logged"}
    except Exception as e:
        print(f"❌ Feedback Error: {e}")
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)