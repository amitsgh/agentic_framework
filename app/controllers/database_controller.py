"""Controller for database operations (save, delete, fetch)"""

from typing import List

from app.services.db.factory import get_db_instance
from app.services.embedder.base import BaseEmbeddings
from app.models.document_model import Document
from app.core.logger import setuplog

logger = setuplog(__name__)


class DatabaseController:
    """Database Controller"""

    def __init__(self):
        self.db = get_db_instance()
        self.db.connect()

    def add_documents_to_db(
        self, documents: List[Document], embeddings: BaseEmbeddings
    ) -> List[str]:
        """Add chunked document to vector db"""

        if not documents:
            logger.warning("No documents provided for saving")
            raise

        try:
            ids = self.db.add_documents(documents, embeddings)
            logger.info("Successfully saved %d documents to Redis.", len(ids))
            return ids

        except Exception as e:
            logger.error("Error saving documents: %s", str(e))
            raise

    def search_documents(
        self, query: str, embeddings: BaseEmbeddings, top_k: int = 10
    ) -> List[Document]:
        """Search for similar documents"""

        try:
            results = self.db.similarity_search(
                query=query, embeddings=embeddings, top_k=top_k
            )
            logger.info(
                "Found %d matching documents for query: '%s'", len(results), query
            )
            return results

        except Exception as e:
            logger.error("Error during document search: %s", str(e))
            raise

    # def delete_documents_by_id(self, document_ids: List[str]) -> bool:
    #     """Delete specific documents by their IDs"""

    #     try:
    #         success = self.db.delete_documents_by_id(document_ids)
    #         logger.info("Deleted documents by ID: %s", document_ids)
    #         return success

    #     except Exception as e:
    #         logger.error("Error deleting documents by ID: %s", str(e))
    #         raise

    def delete_all_documents(self) -> int:
        """Delete all documents from vector db"""

        try:
            count = self.db.delete_all()
            logger.info("Deleted %d documents from Redis Vector Store", count)
            return count

        except Exception as e:
            logger.error("Error deleting all documents: %s", str(e))
            raise
