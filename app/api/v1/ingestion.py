import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.vector_store import vector_store
from app.models.document import Document, DocumentChunk
from app.schemas.ingestion import DocumentIngestResponse, DocumentDetailResponse
from app.services.text_extractor import TextExtractorService
from app.services.chunker import chunker_service, ChunkingStrategy
from app.services.embeddings import embedding_service

router = APIRouter(prefix="/documents", tags=["Document Ingestion API"])


@router.post("/ingest", response_model=DocumentIngestResponse, status_code=201)
async def ingest_document(
    file: UploadFile = File(..., description="Select a .pdf or .txt file to upload"),
    chunk_strategy: ChunkingStrategy = Form(
        ChunkingStrategy.FIXED_SIZE,
        description="Select chunking strategy: fixed_size or recursive_semantic"
    ),
    chunk_size: int = Form(500, ge=100, le=4000, description="Max characters/tokens per chunk"),
    chunk_overlap: int = Form(50, ge=0, le=1000, description="Overlap between consecutive chunks"),
    db: Session = Depends(get_db)
):
    """
    Ingest a document (.pdf or .txt):
    1. Extract plain text content
    2. Apply selected chunking strategy (fixed_size or recursive_semantic)
    3. Generate embeddings
    4. Index vectors in Vector DB (Qdrant/Pinecone)
    5. Save metadata into SQL Database
    """
    filename = file.filename or "unknown.txt"
    file_type = "pdf" if filename.endswith(".pdf") else "txt"

    # Extract text from uploaded document
    extracted_text = await TextExtractorService.extract_text(file)

    # Chunk text according to requested strategy
    chunks = chunker_service.chunk_text(
        text=extracted_text,
        strategy=chunk_strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks generated from document content.")

    # Generate embeddings and store vectors in Qdrant
    chunk_texts = [c.content for c in chunks]
    vectors = embedding_service.generate_embeddings(chunk_texts)

    doc_id = str(uuid.uuid4())
    vector_payloads = [
        {
            "document_id": doc_id,
            "filename": filename,
            "chunk_index": c.chunk_index,
            "content": c.content,
            "token_count": c.token_count
        }
        for c in chunks
    ]
    vector_ids = vector_store.upsert_vectors(vectors=vectors, payloads=vector_payloads)

    # Persist document metadata and chunk records in SQL database
    now_utc = datetime.now(timezone.utc)
    doc_record = Document(
        id=doc_id,
        filename=filename,
        file_type=file_type,
        total_chunks=len(chunks),
        chunk_strategy=chunk_strategy.value,
        created_at=now_utc
    )
    db.add(doc_record)

    for i, c in enumerate(chunks):
        chunk_record = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=doc_id,
            chunk_index=c.chunk_index,
            content=c.content,
            token_count=c.token_count,
            vector_id=vector_ids[i] if i < len(vector_ids) else None,
            created_at=now_utc
        )
        db.add(chunk_record)

    db.commit()
    db.refresh(doc_record)

    return DocumentIngestResponse(
        document_id=doc_id,
        filename=filename,
        file_type=file_type,
        total_chunks=len(chunks),
        chunk_strategy=chunk_strategy,
        message=f"Successfully ingested {filename} into {len(chunks)} chunks using {chunk_strategy.value} strategy.",
        created_at=doc_record.created_at
    )


@router.get("", response_model=List[DocumentIngestResponse])
def list_documents(db: Session = Depends(get_db)):
    """List all ingested documents and their metadata."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        DocumentIngestResponse(
            document_id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            total_chunks=d.total_chunks,
            chunk_strategy=ChunkingStrategy(d.chunk_strategy),
            message="Ingested",
            created_at=d.created_at
        )
        for d in docs
    ]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document_details(document_id: str, db: Session = Depends(get_db)):
    """Retrieve full details and metadata chunks for a given document ID."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc
