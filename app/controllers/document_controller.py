"""Controller for Document Ingestion"""

import json
from typing import List, Union

from app.services.extractor.factory import get_extractor_instance
from app.services.chunker.factor import get_chunker_instance
from app.models.document_model import Document
from app.core.decorator.timer import timer
from app.core.logger import setuplog

logger = setuplog(__name__)


class DocumentController:
    """Document processing - parsing, chunking, embedding"""

    def __init__(self):
        self.extractor = get_extractor_instance()
        self.chunker = get_chunker_instance()

    def create_documents(self, file_paths: Union[str, List[str]]) -> List[Document]:
        """Parse document and return Document Object"""

        try:
            raw_data = self.extractor.extract(file_paths)
            documents = self.chunker.chunk(raw_data)
            
            if not documents:
                raise ValueError("Parser return no documents")

            logger.info("Created %s: %d", file_paths, len(documents))
            return documents

        except Exception as e:
            logger.error("Parsing error for %s: %s", file_paths, str(e))
            raise
