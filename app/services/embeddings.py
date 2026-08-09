import hashlib
import logging
from typing import List
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service to generate dense vector embeddings for text chunks and query strings."""

    def __init__(self) -> None:
        self.dimension = settings.EMBEDDING_DIMENSION
        self.model = settings.EMBEDDING_MODEL
        self.use_mock = settings.USE_MOCK_LLM or settings.OPENAI_API_KEY.startswith("sk-fake")

        if not self.use_mock:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
            logger.info("EmbeddingService running in Mock Mode (Deterministic vector embeddings enabled).")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of text strings."""
        if not texts:
            return []

        if not self.use_mock and self.client:
            try:
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.model
                )
                return [data.embedding for data in response.data]
            except Exception as e:
                logger.error(f"OpenAI embedding generation failed ({e}). Falling back to mock embeddings.")

        # Fallback / Mock Embedding Generator
        return [self._generate_mock_vector(t) for t in texts]

    def generate_single_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for a single text string."""
        return self.generate_embeddings([text])[0]

    def _generate_mock_vector(self, text: str) -> List[float]:
        """Create a deterministic normalized float vector derived from text hash for testing."""
        vector = []
        for i in range(self.dimension):
            hash_input = f"{text}_{i}".encode('utf-8')
            sha = hashlib.sha256(hash_input).hexdigest()
            # Convert first 8 hex characters to float in range [-1.0, 1.0]
            val = (int(sha[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            vector.append(val)
        
        # Normalize vector length to 1.0 for Cosine distance
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector


embedding_service = EmbeddingService()
