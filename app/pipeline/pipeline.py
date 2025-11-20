"""Document processing pipeline - MinIO-based"""

from typing import List

from app.services.extractor.base import BaseExtractor
from app.services.chunker.base import BaseChunker
from app.services.storage.minio_storage import MinIOStorage
from app.models.document_model import Document, DocumentMetadata
from app.models.processing_state import ProcessingStage, ProcessingState
from app.manager.state_manager import StateManager
from app.exceptions import DocumentProcessingError
from app.utils.logger import setuplog

logger = setuplog(__name__)


class DocumentPipeline:
    """Orchestrates document processing pipeline with MinIO"""

    def __init__(
        self,
        extractor: BaseExtractor,
        chunker: BaseChunker,
        state_manager: StateManager,
        storage: MinIOStorage,
    ):
        self.extractor = extractor
        self.chunker = chunker
        self.state_manager = state_manager
        self.storage = storage

    def process(
        self, file_hash: str, force_reprocess: bool = False
    ) -> tuple[List[Document], ProcessingState]:
        """Process documents through pipeline - all stages read/write from MinIO"""

        # Get current state
        state = self.state_manager.get_state(file_hash)
        if not state:
            raise DocumentProcessingError(f"No state found for file_hash: {file_hash}")

        try:
            # Stage 1: EXTRACT
            if state.stage == ProcessingStage.UPLOADED or force_reprocess:
                logger.info("Stage: EXTRACT - Reading raw file from MinIO")
                raw_path = state.get_artifact_path("raw")
                if not raw_path:
                    raise DocumentProcessingError("Raw file path not found in state")

                # Download raw file temporarily for extraction
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_path = tmp_file.name
                    self.storage.download_file(raw_path, tmp_path)

                try:
                    extracted_documents = self.extractor.extract_data([tmp_path])
                    if not extracted_documents:
                        raise DocumentProcessingError("Extractor returned no data")

                    # Store extracted JSON in MinIO
                    extracted_data = [
                        {
                            "content": doc.content,
                            "metadata": doc.metadata.model_dump(mode="json") if doc.metadata else None
                        }
                        for doc in extracted_documents
                    ]
                    extracted_path = self.storage.get_object_path("extracted", file_hash)
                    self.storage.upload_json(extracted_data, extracted_path)

                    # Update state
                    state = self.state_manager.update_stage(
                        state, ProcessingStage.EXTRACTED, artifact_path=("extracted", extracted_path)
                    )
                    logger.info("Extraction completed: %d documents", len(extracted_documents))
                finally:
                    # Clean up temp file
                    import os
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

            # Stage 2: CHUNK
            if state.stage == ProcessingStage.EXTRACTED or (
                state.stage == ProcessingStage.UPLOADED and force_reprocess
            ):
                logger.info("Stage: CHUNK - Reading extracted data from MinIO")
                extracted_path = state.get_artifact_path("extracted")
                if not extracted_path:
                    raise DocumentProcessingError("Extracted data path not found in state")

                # Download extracted JSON
                extracted_data = self.storage.download_json(extracted_path)

                # Reconstruct Document objects
                extracted_documents = []
                for item in extracted_data:
                    if isinstance(item, dict):
                        content = item.get("content", "")
                        metadata_dict = item.get("metadata")
                        metadata = DocumentMetadata(**metadata_dict) if metadata_dict else None
                        extracted_documents.append(Document(content=content, metadata=metadata))

                # Chunk documents
                chunked_documents = self.chunker.chunk(extracted_documents)
                if not chunked_documents:
                    raise DocumentProcessingError("Chunker returned no documents")

                # Store chunks JSON in MinIO
                chunks_data = [
                    {
                        "content": doc.content,
                        "metadata": doc.metadata.model_dump(mode="json") if doc.metadata else None
                    }
                    for doc in chunked_documents
                ]
                chunks_path = self.storage.get_object_path("chunks", file_hash)
                self.storage.upload_json(chunks_data, chunks_path)

                # Update state
                state = self.state_manager.update_stage(
                    state, ProcessingStage.CHUNKED, artifact_path=("chunks", chunks_path)
                )
                logger.info("Chunking completed: %d chunks", len(chunked_documents))

            # Load chunks for return (only if we have chunks path)
            chunks_path = state.get_artifact_path("chunks")
            if chunks_path:
                chunks_data = self.storage.download_json(chunks_path)
                chunked_documents = []
                for item in chunks_data:
                    if isinstance(item, dict):
                        content = item.get("content", "")
                        metadata_dict = item.get("metadata")
                        metadata = DocumentMetadata(**metadata_dict) if metadata_dict else None
                        chunked_documents.append(Document(content=content, metadata=metadata))

                logger.info(
                    "Pipeline completed: %d chunks from file_hash %s",
                    len(chunked_documents),
                    file_hash[:16],
                )
                return chunked_documents, state
            else:
                # If state is STORED but chunks path is missing, document is already in DB
                # Return empty list - chunks are in vector DB, not in MinIO
                if state.stage == ProcessingStage.STORED:
                    logger.info(
                        "Document already stored in DB, chunks path not in state: %s",
                        file_hash[:16],
                    )
                    return [], state
                else:
                    # For other stages, chunks path should exist
                    raise DocumentProcessingError("Chunks path not found in state")

        except DocumentProcessingError:
            raise
        except Exception as e:
            logger.error("Pipeline error: %s", str(e), exc_info=True)
            state = self.state_manager.update_stage(
                state, ProcessingStage.FAILED, error_message=str(e)
            )
            raise DocumentProcessingError(f"Pipeline failed: {str(e)}") from e
