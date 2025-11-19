"""State manager - manages processing state lifecycle"""

from typing import Optional
from datetime import datetime, timezone

from app.repositories.cache_repository import CacheRepository
from app.services.cache.base import BaseCache
from app.models.processing_state import ProcessingStage, ProcessingState
from app.utils.logger import setuplog

logger = setuplog(__name__)


class StateManager:
    """Manages document processing state"""

    def __init__(self, cache: BaseCache):
        self.cache_repository = CacheRepository(cache)
        self.cache = cache
        self.processing_ttl = 86400 * 7  # 7 days

    def get_state(self, file_hash: str) -> Optional[ProcessingState]:
        """Get current processing state"""
        return self.cache_repository.get(file_hash)

    def create_state(
        self, file_hash: str, filename: str, raw_artifact_path: str
    ) -> ProcessingState:
        """Create new processing state"""
        state = ProcessingState(
            file_hash=file_hash,
            filename=filename,
            stage=ProcessingStage.UPLOADED,
            artifact_paths={"raw": raw_artifact_path},
            created_at=datetime.now(timezone.utc).isoformat(),
            error_message=None,
            updated_at=None,
        )
        self.cache_repository.save(state)
        return state

    def update_stage(
        self,
        state: ProcessingState,
        stage: ProcessingStage,
        error_message: Optional[str] = None,
        artifact_path: Optional[tuple[str, str]] = None,
    ) -> ProcessingState:
        """Update processing stage with validation"""
        if not state.stage.can_transition_to(stage):
            raise ValueError(
                f"Invalid stage transition: {state.stage.value} -> {stage.value}"
            )

        state.stage = stage
        state.updated_at = datetime.now(timezone.utc).isoformat()

        if error_message:
            state.error_message = error_message
        elif state.stage != ProcessingStage.FAILED:
            state.error_message = None

        # Update artifact path if provided
        if artifact_path:
            artifact_type, path = artifact_path
            state.set_artifact_path(artifact_type, path)

        self.cache_repository.save(state)
        return state

    def clear_file_cache(self, file_hash: str) -> bool:
        """Clear all cache entries for a file"""
        try:
            return self.cache_repository.delete(file_hash)
        except Exception as e:
            logger.warning("Error clearing file state: %s", str(e))
            return False
