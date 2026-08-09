from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique identifier for user multi-turn session")
    message: str = Field(..., description="User message or query")
    top_k: int = Field(default=4, ge=1, le=10, description="Number of vector context chunks to retrieve")


class SourceChunk(BaseModel):
    document_id: str
    filename: str
    content: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[SourceChunk] = []
    booking_info: Optional[Dict[str, Any]] = None
