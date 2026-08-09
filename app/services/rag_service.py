import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from openai import OpenAI

from app.core.config import settings
from app.core.redis import redis_manager
from app.core.vector_store import vector_store
from app.services.embeddings import embedding_service
from app.services.booking_service import booking_service

logger = logging.getLogger(__name__)


class ConversationalRAGService:
    """Custom RAG Engine managing Redis history, Vector Retrieval, LLM Synthesis, & Interview Booking."""

    def __init__(self) -> None:
        self.use_mock = settings.USE_MOCK_LLM or settings.OPENAI_API_KEY.startswith("sk-fake")
        if not self.use_mock:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None

    def process_message(
        self,
        db: Session,
        session_id: str,
        user_message: str,
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        Process a multi-turn user message:
        1. Fetch chat history from Redis memory
        2. Detect interview booking intent
        3. Retrieve vector context from Qdrant/Vector Store
        4. Synthesize final answer via LLM (No RetrievalQAChain used)
        5. Save message turn to Redis
        """
        history = redis_manager.get_history(session_id=session_id, limit=6)
        booking_info = self._check_and_handle_booking(db, user_message)

        query_vector = embedding_service.generate_single_embedding(user_message)
        retrieved_chunks = vector_store.search_similar(query_vector=query_vector, top_k=top_k)

        context_str = self._build_context_string(retrieved_chunks)
        history_str = self._build_history_string(history)

        if booking_info and booking_info.get("is_created"):
            llm_response = (
                f"Great news! Your interview has been successfully scheduled for "
                f"{booking_info['booking_date']} at {booking_info['booking_time']}. "
                f"A confirmation email will be sent to {booking_info['candidate_email']}.\n\n"
            )
            llm_response += self._generate_llm_answer(user_message, history_str, context_str)
        elif self._is_booking_request(user_message):
            llm_response = (
                "I would be happy to help you schedule an interview! "
                "Please provide your **Full Name**, **Email Address**, **Preferred Date (YYYY-MM-DD)**, and **Time**."
            )
        else:
            llm_response = self._generate_llm_answer(user_message, history_str, context_str)

        redis_manager.push_message(session_id=session_id, role="user", content=user_message)
        redis_manager.push_message(session_id=session_id, role="assistant", content=llm_response)

        # Format sources
        sources = [
            {
                "document_id": chunk.get("document_id", ""),
                "filename": chunk.get("filename", "unknown"),
                "content": chunk.get("content", "")[:200] + "...",
                "score": chunk.get("_score", 0.0)
            }
            for chunk in retrieved_chunks
        ]

        return {
            "session_id": session_id,
            "answer": llm_response,
            "sources": sources,
            "booking_info": booking_info
        }

    def _check_and_handle_booking(self, db: Session, user_message: str) -> Optional[Dict[str, Any]]:
        extracted = booking_service.extract_booking_details_from_text(user_message)
        if extracted and extracted.get("is_complete"):
            booking = booking_service.create_booking(
                db=db,
                candidate_name=extracted["candidate_name"],
                candidate_email=extracted["candidate_email"],
                booking_date=extracted["booking_date"],
                booking_time=extracted["booking_time"],
                notes="Booked via Conversational RAG Bot"
            )
            return {
                "booking_id": booking.id,
                "candidate_name": booking.candidate_name,
                "candidate_email": booking.candidate_email,
                "booking_date": booking.booking_date,
                "booking_time": booking.booking_time,
                "is_created": True
            }
        return None

    def _is_booking_request(self, message: str) -> bool:
        keywords = ["book interview", "schedule interview", "interview slot", "book an interview", "schedule a chat"]
        return any(k in message.lower() for k in keywords)

    def _build_context_string(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "No relevant external documents found."
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            filename = chunk.get("filename", "Document")
            content = chunk.get("content", "")
            formatted.append(f"--- Document Chunk {i} [{filename}] ---\n{content}")
        return "\n\n".join(formatted)

    def _build_history_string(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return "No prior messages."
        lines = []
        for h in history:
            role = "User" if h.get("role") == "user" else "Assistant"
            lines.append(f"{role}: {h.get('content', '')}")
        return "\n".join(lines)

    def _generate_llm_answer(self, query: str, history: str, context: str) -> str:
        if not self.use_mock and self.client:
            try:
                system_prompt = (
                    "You are an expert AI assistant specializing in document retrieval and interview scheduling. "
                    "Use the provided Document Context to answer user questions accurately. "
                    "If the answer is not contained within the context, use your general knowledge but mention that "
                    "it is outside the ingested documents."
                )
                user_prompt = (
                    f"Chat History:\n{history}\n\n"
                    f"Document Context:\n{context}\n\n"
                    f"Current User Question: {query}\n\n"
                    f"Answer:"
                )
                response = self.client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )
                return response.choices[0].message.content or "No response generated."
            except Exception as e:
                logger.error(f"LLM generation error ({e}). Using context synthesizer.")

        # Standalone / Mock Synthesis
        if "No relevant external documents" not in context:
            first_chunk_sample = context.split("---")[1].strip() if "---" in context else context[:300]
            return f"Based on your documents:\n\n{first_chunk_sample[:400]}...\n\n(Synthesized from document context for query: '{query}')"
        else:
            return f"I analyzed your query '{query}', but no relevant information was found in the ingested documents. How else may I assist you?"


rag_service = ConversationalRAGService()
