import logging
import uuid
from typing import Any, List, Dict
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreInterface:
    """Interface for vector database operations (Qdrant & Pinecone compliant)."""

    def __init__(self) -> None:
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_size = settings.EMBEDDING_DIMENSION
        self.client: QdrantClient = None
        self._init_qdrant()

    def _init_qdrant(self) -> None:
        """Initialize Qdrant client (supports :memory: or remote server)."""
        if settings.QDRANT_LOCATION == ":memory:":
            self.client = QdrantClient(location=":memory:")
            logger.info("Qdrant initialized in memory mode.")
        else:
            self.client = QdrantClient(
                url=settings.QDRANT_LOCATION,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
            )
            logger.info(f"Qdrant client connected to {settings.QDRANT_LOCATION}")

        # Ensure collection exists
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.vector_size,
                    distance=qmodels.Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection '{self.collection_name}'.")

    def upsert_vectors(
        self,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: List[str] = None
    ) -> List[str]:
        """Upsert vectors into vector store with metadata payloads."""
        if not ids:
            ids = [str(uuid.uuid4()) for _ in vectors]

        points = [
            qmodels.PointStruct(
                id=vector_id,
                vector=vector,
                payload=payload
            )
            for vector_id, vector, payload in zip(ids, vectors, payloads)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        return ids

    def search_similar(
        self,
        query_vector: List[float],
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """Perform vector search and return top matched chunk metadata."""
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k
        )

        results: List[Dict[str, Any]] = []
        for point in search_result.points:
            payload = point.payload or {}
            payload["_id"] = str(point.id)
            payload["_score"] = float(point.score) if point.score else 0.0
            results.append(payload)

        return results


vector_store = VectorStoreInterface()
