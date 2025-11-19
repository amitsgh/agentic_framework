# app/controllers/document_controller.py
"""Document controller - orchestration only"""
from typing import List, Tuple
from app.pipeline.pipeline import DocumentPipeline
from app.manager.state_manager import StateManager
from app.repositories.document_repository import DocumentRepository
from app.services.embedder.base import BaseEmbeddings
from app.models.document_model import Document
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
    ):
        self.pipeline = pipeline
        self.state_manager = state_manager
        self.document_repository = document_repository
    
    def upload(
        self,
        file_path: str,
        file_hash: str,
        embeddings: BaseEmbeddings,
        forced_reprocess: bool = False,
    ) -> Tuple[List[Document], ProcessingState]:
        """Orchestrate document upload and processing"""
        
        # Check if already fully processed
        if not forced_reprocess:
            state = self.state_manager.get_state(file_hash)
            if state and state.stage == ProcessingStage.STORED:
                logger.info("Document already fully processed: %s", file_hash[:16])
                # Still need to return documents for response
                chunked_docs = self.state_manager.load_chunked_docs(file_hash)
                if chunked_docs:
                    return chunked_docs, state
        
        # Process through pipeline
        documents, state = self.pipeline.process(
            file_paths=[file_path],
            file_hash=file_hash,
            force_reprocess=forced_reprocess,
        )
        
        # Store in vector database if not already stored
        if state.stage != ProcessingStage.STORED:
            try:
                self.document_repository.add_documents(documents, embeddings)
                state = self.state_manager.update_stage(state, ProcessingStage.STORED)
                logger.info("Documents stored successfully: %d chunks", len(documents))
            except DatabaseError:
                # Re-raise DatabaseError as-is (already logged in repository)
                state = self.state_manager.update_stage(
                    state, ProcessingStage.FAILED, error_message="Database error occurred"
                )
                raise
        
        return documents, state
    
    def delete_all(self) -> int:
        """Delete all documents from database"""
        return self.document_repository.delete_all()