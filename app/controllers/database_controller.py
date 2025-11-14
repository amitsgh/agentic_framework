"""Controller for database operations (save, delete, fetch)"""

from typing import List

from app.services.db.base import BaseDB
from app.services.embedder.base import BaseEmbeddings
from app.models.document_model import Document
from app.core.logger import setuplog
from app.core.exceptions.base import DatabaseError

logger = setuplog(__name__)


class DatabaseController:
    """Database Controller"""

    def __init__(self, db: BaseDB):
        self.db = db

    def add_documents_to_db(
        self, documents: List[Document], embeddings: BaseEmbeddings
    ) -> List[str]:
        """Add chunked document to vector db"""

        if not documents:
            logger.warning("No documents provided for saving")
            raise DatabaseError("No documents provided")

        try:
            ids = self.db.add_documents(documents, embeddings)
            logger.info("Successfully saved %d documents to Redis.", len(ids))
            return ids

        except Exception as e:
            logger.error("Error saving documents: %s", str(e), exc_info=True)
            raise DatabaseError(f"Failed to save documents: {str(e)}") from e

    def search_documents(
        self, query: str, embeddings: BaseEmbeddings, top_k: int = 10
    ) -> List[Document]:
        """Search for similar documents"""

        if not query or not query.strip():
            raise DatabaseError("Empty query provided")

        try:
            results = self.db.similarity_search(
                query=query, embeddings=embeddings, top_k=top_k
            )
            logger.info(
                "Found %d matching documents for query: '%s'", len(results), query
            )
            return results

        except Exception as e:
            logger.error("Error during document search: %s", str(e), exc_info=True)
            raise DatabaseError(f"Search failed: {str(e)}") from e

    def delete_all_documents(self) -> int:
        """Delete all documents from vector db"""

        try:
            count = self.db.delete_all()
            logger.info("Deleted %d documents from Redis Vector Store", count)
            return count

        except Exception as e:
            logger.error("Error deleting all documents: %s", str(e), exc_info=True)
            raise DatabaseError(f"Failed to delete documents: {str(e)}") from e
