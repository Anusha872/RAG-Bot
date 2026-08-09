import json
import logging
from typing import Any, List, Optional
import redis
import fakeredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis connection manager with automatic fallback to fakeredis for zero-dependency execution."""

    def __init__(self) -> None:
        self.client: Any = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        if settings.REDIS_URL:
            try:
                client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
                client.ping()
                self.client = client
                logger.info("Connected to Redis server successfully.")
                return
            except Exception as e:
                logger.warning(f"Could not connect to Redis server at {settings.REDIS_URL} ({e}). Falling back to fakeredis.")
        
        # Fallback to fakeredis
        self.client = fakeredis.FakeStrictRedis(decode_responses=True)
        logger.info("Initialized in-memory FakeRedis fallback client.")

    def push_message(self, session_id: str, role: str, content: str) -> None:
        """Push a conversation turn to session history."""
        key = f"chat_history:{session_id}"
        message_data = json.dumps({"role": role, "content": content})
        self.client.rpush(key, message_data)

    def get_history(self, session_id: str, limit: int = 10) -> List[dict[str, str]]:
        """Retrieve recent conversation history for session."""
        key = f"chat_history:{session_id}"
        items = self.client.lrange(key, -limit, -1)
        history: List[dict[str, str]] = []
        for item in items:
            try:
                history.append(json.loads(item))
            except json.JSONDecodeError:
                continue
        return history

    def clear_history(self, session_id: str) -> None:
        """Clear conversation history for session."""
        key = f"chat_history:{session_id}"
        self.client.delete(key)


redis_manager = RedisManager()
