"""State Cache Repository - handle cache operations"""

from typing import Optional
from app.services.cache.base import BaseCache
from app.models.processing_state import ProcessingState
from app.utils.logger import setuplog

logger = setuplog(__name__)


class CacheRepository:
    """Repository for processing state operations"""

    def __init__(self, cache: Optional[BaseCache]):
        self.cache = cache
        self.state_ttl = 86400 * 7  # 7 days

    def _get_state_key(self, file_hash: str) -> str:
        """Generate state cache key"""
        key_pattern = f"doc_state:{file_hash}"
        return key_pattern

    def get(self, file_hash: str) -> Optional[ProcessingState]:
        """Load processing state from cache"""
        if not self.cache:
            return None

        try:
            state_key = self._get_state_key(file_hash)
            state_data = self.cache.get(state_key)
            if state_data:
                return ProcessingState(**state_data)
        except Exception as e:
            logger.warning("Error loading state from cache: %s", str(e))

        return None

    def save(self, state: ProcessingState) -> bool:
        """Save processing state in cache"""
        if not self.cache:
            return False

        try:
            from datetime import datetime, timezone

            state.updated_at = datetime.now(timezone.utc).isoformat()
            return self.cache.set(
                self._get_state_key(state.file_hash),
                state.model_dump(mode="json"),
                ttl=self.state_ttl,
            )
        except Exception as e:
            logger.warning("Error saving state to cache: %s", str(e))
            return False

    def delete(self, file_hash: str) -> bool:
        """Delete state from cache"""
        if not self.cache:
            return False
        
        try:
            return self.cache.delete(self._get_state_key(file_hash))
        except Exception as e:
            logger.warning("Error deleting state from cache: %s", str(e))
            return False