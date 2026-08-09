from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.redis import redis_manager
from app.schemas.rag import ChatRequest, ChatResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["Conversational RAG API"])


@router.post("", response_model=ChatResponse)
def chat_with_rag(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Conversational RAG endpoint:
    - Custom RAG (no RetrievalQAChain)
    - Redis chat memory for multi-turn sessions
    - Vector context retrieval
    - Interview booking detection & processing
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    result = rag_service.process_message(
        db=db,
        session_id=payload.session_id,
        user_message=payload.message,
        top_k=payload.top_k
    )

    return ChatResponse(**result)


@router.delete("/{session_id}")
def reset_chat_session(session_id: str):
    """Clear Redis conversation history for a session."""
    redis_manager.clear_history(session_id)
    return {"message": f"Chat history cleared for session '{session_id}'."}


@router.get("/{session_id}/history")
def get_chat_history(session_id: str):
    """Retrieve full conversation history from Redis memory."""
    history = redis_manager.get_history(session_id=session_id, limit=50)
    return {"session_id": session_id, "messages": history}
