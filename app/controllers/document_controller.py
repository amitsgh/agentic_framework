"""Controller for Document Ingestion"""

from typing import List, Union

from app.services.extractor.base import BaseExtractor
from app.services.chunker.base import BaseChunker
from app.models.document_model import Document
from app.core.decorator.timer import timer
from app.core.logger import setuplog
from app.core.exceptions.base import DocumentProcessingError

logger = setuplog(__name__)


class DocumentController:
    """Document processing - parsing, chunking"""

    def __init__(self, extractor: BaseExtractor, chunker: BaseChunker):
        self.extractor = extractor
        self.chunker = chunker

    @timer
    def create_documents(self, file_paths: Union[str, List[str]]) -> List[Document]:
        """Parse document and return Document Object"""

        if not file_paths:
            raise DocumentProcessingError("No file paths provided")

        try:
            if isinstance(file_paths, str):
                file_paths = [file_paths]

            extracted_documents = self.extractor.extract(file_paths)
            logger.debug("Extracted documents with %d pages", len(extracted_documents))

            if not extracted_documents:
                raise DocumentProcessingError("Extractor returned no data")

            chunked_documents = self.chunker.chunk(extracted_documents)

            if not chunked_documents:
                raise DocumentProcessingError("Chunker returned no documents")

            logger.info(
                "Created %d documents from %d files",
                len(chunked_documents),
                len(file_paths),
            )
            return chunked_documents

        except DocumentProcessingError:
            raise
        except Exception as e:
            logger.error("Parsing error for %s: %s", file_paths, str(e), exc_info=True)
            raise DocumentProcessingError(
                f"Failed to process documents: {str(e)}"
            ) from e
