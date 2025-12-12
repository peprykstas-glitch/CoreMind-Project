import time
import traceback
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

# Project modules
from app.vector_store import vector_db
from app.config import settings
from app.schemas import QueryRequest, QueryResponse
from app.parser import parse_file

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(f"🔌 Connecting to Ollama at: {settings.OLLAMA_HOST}")
print(f"🤖 Using Model: {settings.OLLAMA_MODEL}")

client = AsyncOpenAI(
    base_url=settings.OLLAMA_HOST,
    api_key="ollama"
)

@app.get("/health")
async def health_check():
    """Health check endpoint to verify backend and DB status."""
    try:
        info = vector_db.client.get_collection(vector_db.collection_name)
        db_status = f"Connected. Docs count: {info.points_count}"
    except Exception as e:
        db_status = f"Error: {str(e)}"

    return {
        "status": "ok", 
        "model": settings.OLLAMA_MODEL,
        "database": db_status
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads and indexes a file into the Vector DB."""
    start_time = time.time()
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    print(f"📥 Uploading file: {file.filename}")
    text_content = await parse_file(file)
    
    if not text_content.strip():
        raise HTTPException(status_code=400, detail="Empty file or parse error")

    try:
        doc_id = vector_db.add_document(
            text=text_content, 
            meta={"filename": file.filename}
        )
    except Exception as e:
        print(f"❌ Indexing Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

    duration = time.time() - start_time
    print(f"✅ File indexed. Duration: {duration:.2f}s")
    
    return {
        "status": "success",
        "doc_id": doc_id,
        "filename": file.filename,
        "duration": duration
    }

@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """Processes user query using RAG pipeline."""
    start_time = time.time()
    user_query = request.messages[-1].content
    print(f"💬 Query received: {user_query}")
    
    try:
        # 1. Retrieve context from Qdrant
        search_results = vector_db.search(user_query, limit=3)
        
        context_parts = []
        for hit in search_results:
            source = hit.payload.get('filename', 'Unknown')
            text = hit.payload.get('content', '')
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

    # 2. System Prompt (Professional & Standard)
    system_prompt = (
        "You are CoreMind, an advanced AI assistant designed for document analysis. "
        "Your goal is to provide accurate, professional answers based ONLY on the provided context below. "
        "If the answer is not in the context, politely state that you do not have that information. "
        "Do not hallucinate or invent facts.\n\n"
        f"--- CONTEXT ---\n{context_str}"
    )
    
    llm_messages = [{"role": "system", "content": system_prompt}]
    for m in request.messages:
        if m.role != "system":
            llm_messages.append(m.model_dump())

    try:
        # 3. LLM Generation (Updated to use parameters)
        print("⏳ Sending request to Ollama...")
        
        # Use the temperature from the request or the default temperature from the settings
        temp = request.temperature if request.temperature is not None else 0.3
        # Use the model from the request or the default model
        target_model = request.model if request.model else settings.OLLAMA_MODEL

        completion = await client.chat.completions.create(
            model=target_model,
            messages=llm_messages,
            temperature=temp
        )
        response_text = completion.choices[0].message.content
        print("✅ Response received from Ollama.")
        
    except Exception as e:
        print(f"❌ LLM GENERATION ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    latency = time.time() - start_time
    
    sources = [
        {
            "content": hit.payload['content'][:150] + "...", 
            "score": hit.score,
            "filename": hit.payload.get('filename', 'Unknown')
        } 
        for hit in search_results
    ]
    
    return QueryResponse(
        response_text=response_text,
        sources=sources,
        latency=latency
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)