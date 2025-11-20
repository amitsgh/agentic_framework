# app/controllers/document_controller.py
"""Document controller - orchestration only"""
from typing import List, Tuple
import os
from pathlib import Path

from app.pipeline.pipeline import DocumentPipeline
from app.manager.state_manager import StateManager
from app.repositories.document_repository import DocumentRepository
from app.services.embedder.base import BaseEmbeddings
from app.services.storage.minio_storage import MinIOStorage
from app.models.document_model import Document, DocumentMetadata
from app.models.processing_state import ProcessingStage, ProcessingState
from app.exceptions import DatabaseError
from app.utils.logger import setuplog

logger = setuplog(__name__)


class DocumentController:
    """Orchestrates document-related operations"""

    def __init__(
        self,
        pipeline: DocumentPipeline,
        state_manager: StateManager,
        document_repository: DocumentRepository,
        storage: MinIOStorage,
    ):
        self.pipeline = pipeline
        self.state_manager = state_manager
        self.document_repository = document_repository
        self.storage = storage

    def upload(
        self,
        file_path: str,
        file_hash: str,
        filename: str,
        embeddings: BaseEmbeddings,
        forced_reprocess: bool = False,
    ) -> Tuple[List[Document], ProcessingState]:
        """Orchestrate document upload and processing"""

        # Check if already fully processed
        if not forced_reprocess:
            state = self.state_manager.get_state(file_hash)
            if state and state.stage == ProcessingStage.STORED:
                logger.info("Document already fully processed: %s", file_hash[:16])
                # Load chunks from MinIO for response
                chunks_path = state.get_artifact_path("chunks")
                # If chunks path not in state, try to construct it from file_hash
                if not chunks_path:
                    chunks_path = self.storage.get_object_path("chunks", file_hash)
                    logger.debug("Chunks path not in state, constructed from file_hash: %s", chunks_path)
                
                if chunks_path and self.storage.object_exists(chunks_path):
                    chunks_data = self.storage.download_json(chunks_path)
                    documents = []
                    for item in chunks_data:
                        if isinstance(item, dict):
                            content = item.get("content", "")
                            metadata_dict = item.get("metadata")
                            metadata = DocumentMetadata(**metadata_dict) if metadata_dict else None
                            documents.append(Document(content=content, metadata=metadata))
                    return documents, state
                else:
                    # Chunks file doesn't exist in MinIO, but document is stored in DB
                    # This can happen if MinIO was cleared but DB still has embeddings
                    logger.warning("Chunks file not found in MinIO for stored document: %s", file_hash[:16])
                    # Return empty documents list - document is in DB but chunks file is missing
                    return [], state

        # Stage 0: UPLOAD - Save raw file to MinIO
        state = self.state_manager.get_state(file_hash)
        if not state:
            # Upload raw file to MinIO
            raw_path = self.storage.get_object_path("raw", file_hash, extension=Path(file_path).suffix)
            self.storage.upload_file(file_path, raw_path)
            
            # Create state
            state = self.state_manager.create_state(file_hash, filename, raw_path)
            logger.info("Raw file uploaded to MinIO: %s", raw_path)
        else:
            # Update filename if changed
            if state.filename != filename:
                state.filename = filename
                self.state_manager.cache_repository.save(state)

        # Clean up local temp file
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug("Cleaned up local temp file: %s", file_path)
        except Exception as e:
            logger.warning("Failed to clean up temp file: %s", str(e))

        # Process through pipeline
        documents, state = self.pipeline.process(
            file_hash=file_hash,
            force_reprocess=forced_reprocess,
        )

        # Stage 3: EMBED & STORE
        if state.stage == ProcessingStage.CHUNKED:
            try:
                # Embed and store in vector DB
                self.document_repository.add_documents(documents, embeddings)
                state = self.state_manager.update_stage(state, ProcessingStage.STORED)
                logger.info("Documents stored successfully: %d chunks", len(documents))
            except DatabaseError:
                state = self.state_manager.update_stage(
                    state, ProcessingStage.FAILED, error_message="Database error occurred"
                )
                raise

        return documents, state

    def delete_all(self) -> int:
        """Delete all documents from database"""
        return self.document_repository.delete_all()