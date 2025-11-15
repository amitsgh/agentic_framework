"""Controller for Document Ingestion"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from shutil import ExecError
from typing import List, Dict, Union, Optional, Sequence, Any
from datetime import datetime, timezone, timedelta

from app.services.extractor.base import BaseExtractor
from app.services.chunker.base import BaseChunker
from app.services.cache.base import BaseCache
from app.models.document_model import Document
from app.models.processing_state import ProcessingStage, ProcessingState
from app.core.decorator.timer import timer
from app.core.logger import setuplog
from app.core.exceptions.base import DocumentProcessingError
from app.core.config import config

logger = setuplog(__name__)


class DocumentController:
    """Document processing - parsing, chunking"""

    def __init__(
        self,
        extractor: BaseExtractor,
        chunker: BaseChunker,
        cache: Optional[BaseCache] = None,
    ):
        self.extractor = extractor
        self.chunker = chunker
        self.cache = cache

    def _get_cache_key(self, file_hash: str, stage: str) -> str:
        """Generate cache key using config pattern"""
        return config.CACHE_DOC_PROCESSING_PATTERN.format(
            file_hash=file_hash, stage=stage
        )

    def _get_state_key(self, file_hash: str) -> str:
        """Generate state cache key using config pattern"""
        return config.CACHE_DOC_STATE_PATTERN.format(file_hash=file_hash)

    def _load_state(self, file_hash: str) -> Optional[ProcessingState]:
        """Load processing state from cache"""
        if not self.cache:
            return None

        try:
            state_data = self.cache.get(self._get_state_key(file_hash))
            if state_data:
                return ProcessingState(**state_data)
        except Exception as e:
            logger.warning("Error loading state from cache: %s", str(e))

        return None

    def _save_state(self, state: ProcessingState) -> bool:
        """Save processing state to cache"""
        if not self.cache:
            return False

        try:
            state.updated_at = datetime.utcnow().isoformat()
            return self.cache.set(
                self._get_state_key(state.file_hash),
                state.model_dump(),
                ttl=86400 * 7,  # 7 days
            )
        except Exception as e:
            logger.warning("Error saving state to cache: %s", str(e))
            return False

    def _save_extracted_docs(self, file_hash: str, extracted_docs: List) -> bool:
        """Cache extracted documents"""
        if not self.cache:
            return False

        try:
            serialized = [
                doc.model_dump_json() if hasattr(doc, "model_dump_json") else str(doc)
                for doc in extracted_docs
            ]
            return self.cache.set(
                self._get_cache_key(file_hash, "extracted"),
                serialized,
                ttl=86400 * 7,  # 7 days
            )
        except Exception as e:
            logger.warning("Error caching extracted docs: %s", str(e))
            return False

    def _load_extracted_docs(self, file_hash: str) -> Optional[List]:
        """Load extracted documents from cache"""
        if not self.cache:
            return None

        try:
            return self.cache.get(self._get_cache_key(file_hash, "extracted"))
        except Exception as e:
            logger.warning("Error loading extracted docs from cache: %s", str(e))
            return None

    def _save_chunked_docs(self, file_hash: str, chunked_docs: List[Document]) -> bool:
        """Cache chunked documents"""
        if not self.cache:
            return False

        try:
            # Serialize Document objects
            serialized = [doc.model_dump() for doc in chunked_docs]
            return self.cache.set(
                self._get_cache_key(file_hash, "chunked"),
                serialized,
                ttl=86400 * 7,  # 7 days
            )
        except Exception as e:
            logger.warning("Error caching chunked docs: %s", str(e))
            return False

    def _load_chunked_docs(self, file_hash: str) -> Optional[List[Document]]:
        """Load chunked documents from cache"""
        if not self.cache:
            return None

        try:
            cached = self.cache.get(self._get_cache_key(file_hash, "chunked"))
            if cached:
                return [Document(**doc) for doc in cached]
        except Exception as e:
            logger.warning("Error loading chunked docs from cache: %s", str(e))

        return None

    @timer
    def create_documents(
        self, file_paths: Union[str, List[str]], file_hash: str
    ) -> tuple[List[Document], ProcessingState]:
        """Parse document and return Document Object"""

        logger.debug("create_documents called with file_paths: %s, file_hash: %s", 
                    file_paths if isinstance(file_paths, str) else len(file_paths), file_hash[:16])
        
        if not file_paths:
            logger.error("No file paths provided to create_documents")
            raise DocumentProcessingError("No file paths provided")

        if not file_hash:
            logger.error("File hash is required for state tracking")
            raise DocumentProcessingError("File hash is required for state tracking")

        if isinstance(file_paths, str):
            file_paths = [file_paths]

        state = None

        if self.cache:
            state = self._load_state(file_hash)
            if state:
                logger.info(
                    "Resuming processing for file hash: %s at stage: %s",
                    file_hash,
                    state.stage,
                )

        if not state:
            state = ProcessingState(
                file_hash=file_hash,
                filename=Path(file_paths[0]).name if file_paths else "unknown",
                file_path=file_paths[0],
                stage=ProcessingStage.UPLOADED,
                created_at=datetime.now(timezone.utc).isoformat(),
                extracted_docs=[],
                chunked_docs=[],
                error_message=None,
                updated_at=None,
            )

        try:
            # Step 1: Extraction
            extracted_documents = None
            if state and state.stage in [
                ProcessingStage.EXTRACTED,
                ProcessingStage.CHUNKED,
                ProcessingStage.EMBEDDED,
                ProcessingStage.STORED,
            ]:
                logger.info("Skipping extraction - already completed (stage: %s)", state.stage.value)
                # Note: We can't easily deserialize DoclingDocument from cache,
                # but if stage is STORED, we don't need extracted docs for chunking
                # since chunked docs are already cached. For stages EXTRACTED and above,
                # we'll need to re-extract if chunked docs aren't available.
                if state.stage == ProcessingStage.STORED:
                    # If already stored, we don't need to extract again
                    # The chunked documents should be loaded from cache in the next step
                    extracted_documents = []  # Empty list to indicate skip
                else:
                    # For EXTRACTED, CHUNKED, EMBEDDED stages, we may need to re-extract
                    # if chunked docs aren't available
                    extracted_documents = None  # Will trigger re-extraction if needed

            if extracted_documents is None:
                logger.info("Extracting documents...")
                logger.debug("Calling extractor.extract() for %d file(s)", len(file_paths))
                extracted_documents = self.extractor.extract(file_paths)

                if not extracted_documents:
                    logger.error("Extractor returned no data for file_paths: %s", file_paths)
                    raise DocumentProcessingError("Extractor returned no data")
                logger.debug("Extraction successful: %d documents extracted", len(extracted_documents))

                # Cache extracted docs for reference (even though we can't easily deserialize)
                self._save_extracted_docs(file_hash, extracted_documents)
                state.stage = ProcessingStage.EXTRACTED
                state.extracted_docs = [
                    (
                        doc.model_dump()
                        if hasattr(doc, "model_dump")
                        else (
                            json.loads(doc.model_dump_json())
                            if hasattr(doc, "model_dump_json")
                            else {"content": str(doc), "type": type(doc).__name__}
                        )
                    )
                    for doc in extracted_documents
                ]
                self._save_state(state)
                logger.info("Extraction completed and cached")

            # Step 2: Chunk
            chunked_documents = None
            if state.stage in [
                ProcessingStage.CHUNKED,
                ProcessingStage.EMBEDDED,
                ProcessingStage.STORED,
            ]:
                logger.info("Skipping chunking - already completed")
                chunked_documents = self._load_chunked_docs(file_hash)

            if chunked_documents is None:
                logger.info("Chunking documents...")
                logger.debug("Calling chunker.chunk() for %d extracted documents", 
                           len(extracted_documents) if extracted_documents else 0)
                if extracted_documents is None:
                    logger.error("No extracted documents available for chunking")
                    raise DocumentProcessingError(
                        "No extracted documents available for chunking"
                    )

                chunked_documents = self.chunker.chunk(extracted_documents)

                if not chunked_documents:
                    logger.error("Chunker returned no documents")
                    raise DocumentProcessingError("Chunker returned no documents")
                logger.debug("Chunking successful: %d chunks created", len(chunked_documents))

                self._save_chunked_docs(file_hash, chunked_documents)
                state.stage = ProcessingStage.CHUNKED
                state.chunked_docs = [doc.model_dump() for doc in chunked_documents]
                self._save_state(state)
                logger.info("Chunking completed and cached")

            logger.info(
                "Created %d documents from %d files (hash: %s)",
                len(chunked_documents),
                len(file_paths),
                file_hash[:8] if file_hash else "unknown",
            )

            return chunked_documents, state

        except DocumentProcessingError as e:
            logger.error("Document processing error: %s", str(e), exc_info=True)
            logger.debug("Document processing failed for file_hash: %s", file_hash[:16])
            state.stage = ProcessingStage.FAILED
            state.error_message = str(e)
            self._save_state(state)
            raise
        except Exception as e:
            logger.critical("CRITICAL: Parsing error for %s: %s", file_paths, str(e), exc_info=True)
            logger.debug("Critical parsing error for file_hash: %s", file_hash[:16])
            state.stage = ProcessingStage.FAILED
            state.error_message = str(e)
            self._save_state(state)
            raise DocumentProcessingError(
                f"Failed to process documents: {str(e)}"
            ) from e


# class DocumentCacheController:
#     """Document cache controller"""

#     # Cache TTL constants
#     STATE_TTL = int(timedelta(days=7).total_seconds())  # 7 days
#     EXTRACTED_TTL = int(timedelta(days=7).total_seconds())  # 7 days
#     CHUNKED_TTL = int(timedelta(days=7).total_seconds())  # 7 days

#     # Cache key prefixes
#     STATE_KEY_PREFIX = "doc_state:"
#     EXTRACTED_KEY_PREFIX = "doc_extracted:"
#     CHUNKED_KEY_PREFIX = "doc_chunked:"

#     def __init__(self, cache: BaseCache, key_prefix: str = "doc_cache:*"):
#         self.cache = cache
#         self.key_prefix = key_prefix

#     def _make_key(self, prefix: str, file_hash: str, suffix: str = "") -> str:
#         """Generate cache key with prefix"""

#         key = f"{self.key_prefix}:{prefix}{file_hash}"
#         if suffix:
#             key = f"{key}:{suffix}"
#         return key

#     def get_processing_state(self, file_hash: str) -> Optional[ProcessingState]:
#         """Get processing state from cache"""

#         try:
#             key = self._make_key(self.STATE_KEY_PREFIX, file_hash)
#             state_data = self.cache.get(key)

#             if state_data:
#                 if isinstance(state_data, dict):
#                     return ProcessingState(**state_data)
#                 elif isinstance(state_data, str):
#                     return ProcessingState(**json.loads(state_data))

#             return None

#         except Exception as e:
#             logger.warning("Error loading processing state from cache: %s", str(e))
#             return None

#     def save_processing_state(self, state: ProcessingState) -> bool:
#         """Save processing state to cache"""

#         try:
#             state.updated_at = datetime.now(timezone.utc).isoformat()
#             key = self._make_key(self.STATE_KEY_PREFIX, state.file_hash)

#             state_dict = state.model_dump()

#             success = self.cache.set(key, state_dict, ttl=self.STATE_TTL)

#             if success:
#                 logger.debug("Saved processing state for file_hash: %s (stage: %s)", state.file_hash[:16], state.stage.value)
#             else:
#                 logger.warning("Failed to save processing state for file_hash: %s", state.file_hash[:16])

#             return success

#         except Exception as e:
#             logger.error("Error saving processing state to cache: %s", str(e), exc_info=True)
#             return False
