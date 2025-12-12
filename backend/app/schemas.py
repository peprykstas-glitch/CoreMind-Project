from pydantic import BaseModel, Field
from typing import List, Optional, Any

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str

class QueryRequest(BaseModel):
    messages: List[ChatMessage]
    # New fields (optional, so that the old code does not break)
    temperature: Optional[float] = 0.3
    model: Optional[str] = None 

class QueryResponse(BaseModel):
    response_text: str
    sources: List[Any] = []
    latency: float