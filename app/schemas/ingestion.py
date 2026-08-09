from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.services.chunker import ChunkingStrategy


class DocumentChunkSchema(BaseModel):
    id: str
    chunk_index: int
    content: str
    token_count: int
    vector_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentIngestResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    total_chunks: int
    chunk_strategy: ChunkingStrategy
    message: str
    created_at: datetime


class DocumentDetailResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    total_chunks: int
    chunk_strategy: str
    created_at: datetime
    chunks: List[DocumentChunkSchema] = []

    model_config = ConfigDict(from_attributes=True)
