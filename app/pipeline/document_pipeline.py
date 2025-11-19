"""Document processing pipeline"""

from typing import List

from app.services.extractor.base import BaseExtractor
from app.services.chunker.base import BaseChunker
from app.services.storage.base import BaseStorage
from app.models.document_model import Document, DocumentMetadata
from app.models.processing_state import ProcessingStage, ProcessingState
from app.manager.state_manager import StateManager
from app.exceptions import DocumentProcessingError
from app.utils.logger import setuplog

logger = setuplog(__name__)


class DocumentPipeline:
    """Orchestrates document processing pipeline"""

    def __init__(
        self,
        extractor: BaseExtractor,
        chunker: BaseChunker,
        storage: BaseStorage,
        state_manager: StateManager,
    ):
        self.extractor = extractor
        self.chunker = chunker
        self.storage = storage
        self.state_manager = state_manager

    def process(
        self, file_paths: List[str], file_hash: str, force_reprocess: bool = False
    ) -> tuple[List[Document], ProcessingState]:
        """Process documents through pipeline"""

        # # Get or create state
        # state = self.state_manager.get_state(file_hash)
        # if not state:
        #     state = self.state_manager.create_state(
        #         file_hash=file_hash,
        #         filename=Path(file_paths[0]).name if file_paths else "unknown",
        #         file_path=file_paths[0],
        #     )

        # Get current state
        state = self.state_manager.get_state(file_hash)
        if not state:
            raise DocumentProcessingError(f"No state found for file_hash: {file_hash}")

        try:
            # Extraction
            if state.stage == ProcessingStage.UPLOADED or force_reprocess:
                logger.info("Reading raw file from MinIO")
                raw_path = state.get_artifact_path("raw")
                if not raw_path:
                    raise DocumentProcessingError("Raw file path not found in state")

                # Download raw file temporarily for extraction
                import tempfile

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as tmp_file:
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
                            "metadata": doc.metadata.model_dump(mode="json")
                            if doc.metadata
                            else None,
                        }
                        for doc in extracted_documents
                    ]
                    extracted_path = self.storage.get_object_path(
                        "extracted", file_hash
                    )
                    self.storage.upload_json(extracted_data, extracted_path)

                    # Update state
                    state = self.state_manager.update_stage(
                        state,
                        ProcessingStage.EXTRACTED,
                        artifact_path=("extracted", extracted_path),
                    )
                    logger.info(
                        "Extraction completed: %d documents", len(extracted_documents)
                    )

                finally:
                    import os

                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

            # Chunking
            if state.stage == ProcessingStage.EXTRACTED or (
                state.stage == ProcessingStage.UPLOADED and force_reprocess
            ):
                logger.info("Reading extracted data from MinIO")
                extracted_path = state.get_artifact_path("extracted")
                if not extracted_path:
                    raise DocumentProcessingError(
                        "Extracted data path not found in state"
                    )

                # Download extracted JSON
                extracted_data = self.storage.download_json(extracted_path)

                # Store chunks JSON in MinIO
                extracted_documents = [
                    Document(
                        content=item.get("content"),
                        metadata=DocumentMetadata(**item.get("metadata"))
                        if item.get("metadata")
                        else None,
                    )
                    for item in extracted_data
                ]

        except Exception as e:
            logger.error("Pipeline error: %s", str(e), exc_info=True)
            state = self.state_manager.update_stage(
                state, ProcessingStage.FAILED, error_message=str(e)
            )
            raise DocumentProcessingError(f"Pipeline failed: {str(e)}") from e
