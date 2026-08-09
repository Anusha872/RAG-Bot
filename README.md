# FastAPI RAG Backend and Interview Booking System

A FastAPI backend implementing document ingestion with chunking strategies, Qdrant vector storage, custom conversational RAG with Redis session memory, and an LLM interview booking extractor.

## Features

1. Document Ingestion API: Upload PDF or TXT files, chunk using fixed size or recursive semantic strategies, store vectors in Qdrant, and save document metadata in SQL database.
2. Conversational RAG API: Custom RAG implementation without RetrievalQAChain, Redis chat memory for multi-turn conversations, and direct vector retrieval.
3. Interview Booking: Extracts candidate name, email, date, and time from user chat messages and saves booking records in database.

## Technical Requirements & Constraints

* No FAISS or Chroma (uses Qdrant vector database)
* No RetrievalQAChain (custom RAG pipeline)
* No UI (REST APIs only)
* Redis memory for multi-turn chat history with in-memory fallback
* Full typing annotations and structured modular architecture

## Directory Structure

```
.
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── booking.py
│   │   │   ├── chat.py
│   │   │   └── ingestion.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── redis.py
│   │   └── vector_store.py
│   ├── models/
│   │   ├── booking.py
│   │   └── document.py
│   ├── schemas/
│   │   ├── booking.py
│   │   ├── ingestion.py
│   │   └── rag.py
│   └── services/
│       ├── booking_service.py
│       ├── chunker.py
│       ├── embeddings.py
│       ├── rag_service.py
│       └── text_extractor.py
│   ├── main.py
├── tests/
│   ├── conftest.py
│   ├── test_booking.py
│   ├── test_ingestion.py
│   └── test_rag.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── pytest.ini
└── README.md
```

## Setup and Running

1. Install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access Swagger documentation at `http://localhost:8000/docs`.

3. Run with Docker Compose:
```bash
docker-compose up --build
```

4. Run tests:
```bash
pytest -v
```

## API Endpoints

### Document Ingestion
* `POST /api/v1/documents/ingest`
* `GET /api/v1/documents`
* `GET /api/v1/documents/{document_id}`

### Conversational RAG
* `POST /api/v1/chat`
* `GET /api/v1/chat/{session_id}/history`
* `DELETE /api/v1/chat/{session_id}`

### Interview Booking
* `POST /api/v1/bookings`
* `GET /api/v1/bookings`
