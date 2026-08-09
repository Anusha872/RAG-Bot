import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Document RAG Backend"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite:///./rag_app.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Vector Store
    VECTOR_DB_TYPE: str = "qdrant"  # options: qdrant, pinecone
    QDRANT_LOCATION: str = ":memory:"  # ":memory:" or "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION_NAME: str = "documents"

    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "documents"

    # OpenAI & LLM
    OPENAI_API_KEY: str = "sk-fake-key-for-mocking"
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    USE_MOCK_LLM: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
