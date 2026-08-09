import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.chunker import chunker_service, ChunkingStrategy

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chunker_strategies():
    sample_text = (
        "FastAPI is a modern, fast web framework for building APIs with Python.\n\n"
        "It provides high performance and automatic interactive API documentation.\n\n"
        "Retrieval-Augmented Generation (RAG) enhances LLMs by connecting them to external knowledge sources."
    )

    # Strategy 1: Fixed Size
    fixed_chunks = chunker_service.chunk_text(
        text=sample_text,
        strategy=ChunkingStrategy.FIXED_SIZE,
        chunk_size=100,
        chunk_overlap=20
    )
    assert len(fixed_chunks) > 0
    assert fixed_chunks[0].chunk_index == 0

    # Strategy 2: Recursive Semantic
    semantic_chunks = chunker_service.chunk_text(
        text=sample_text,
        strategy=ChunkingStrategy.RECURSIVE_SEMANTIC,
        chunk_size=120,
        chunk_overlap=10
    )
    assert len(semantic_chunks) > 0


def test_ingest_txt_file_fixed_size():
    content = b"This is a sample document for testing the document ingestion API. It contains vector database concepts."
    file_tuple = ("test_doc.txt", io.BytesIO(content), "text/plain")

    response = client.post(
        "/api/v1/documents/ingest",
        files={"file": file_tuple},
        data={
            "chunk_strategy": "fixed_size",
            "chunk_size": 200,
            "chunk_overlap": 20
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test_doc.txt"
    assert data["file_type"] == "txt"
    assert data["chunk_strategy"] == "fixed_size"
    assert data["total_chunks"] >= 1
    assert "document_id" in data


def test_ingest_txt_file_recursive_semantic():
    content = (
        b"Paragraph One: Artificial Intelligence and Machine Learning.\n\n"
        b"Paragraph Two: Vector databases store dense floating-point representations of high-dimensional items.\n\n"
        b"Paragraph Three: Redis provides ultra-low latency key-value storage ideal for session history."
    )
    file_tuple = ("knowledge.txt", io.BytesIO(content), "text/plain")

    response = client.post(
        "/api/v1/documents/ingest",
        files={"file": file_tuple},
        data={
            "chunk_strategy": "recursive_semantic",
            "chunk_size": 150,
            "chunk_overlap": 20
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["chunk_strategy"] == "recursive_semantic"
    assert data["total_chunks"] >= 1


def test_list_and_get_document_details():
    content = b"Document content for list and details testing."
    file_tuple = ("detail_doc.txt", io.BytesIO(content), "text/plain")
    ingest_res = client.post(
        "/api/v1/documents/ingest",
        files={"file": file_tuple},
        data={
            "chunk_strategy": "fixed_size",
            "chunk_size": 200,
            "chunk_overlap": 20
        }
    )
    assert ingest_res.status_code == 201

    list_res = client.get("/api/v1/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) >= 1

    doc_id = docs[0]["document_id"]
    detail_res = client.get(f"/api/v1/documents/{doc_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == doc_id
    assert len(detail["chunks"]) > 0

