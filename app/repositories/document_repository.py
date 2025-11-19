"""Document Repository - handle database operations for documents"""

from typing import List
from app.services.db.base import BaseDB
from app.services.embedder.base import BaseEmbeddings
from app.models.document_model import Document
from app.exceptions import DatabaseError
from app.utils.logger import setuplog

logger = setuplog(__name__)


class DocumentRepository:
    """Repository for document database operations"""

    def __init__(self, db: BaseDB):
        self.db = db

    def add_documents(
        self, documents: List[Document], embeddings: BaseEmbeddings
    ) -> List[str]:
        """Add documents to vector database"""
        if not documents:
            logger.warning("No documents provided for saving")
            raise DatabaseError("No documents provided")

        try:
            ids = self.db.add_documents(documents, embeddings)
            logger.info("Successfully saved %d documents to database", len(ids))
            return ids
        except Exception as e:
            logger.error("Error saving documents: %s", str(e), exc_info=True)
            raise DatabaseError(f"Failed to save documents: {str(e)}") from e

    def similarity_search(
        self, query: str, embeddings: BaseEmbeddings, top_k: int = 5
    ) -> List[Document]:
        """Search for similar documents"""
        if not query or not query.strip():
            logger.warning("Empty query provided for similarity search")
            return []

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

    def delete_all(self) -> int:
        """Delete all documents from database"""
        try:
            count = self.db.delete_all()
            logger.info("Deleted %d documents from database", count)
            return count
        except Exception as e:
            logger.error("Error deleting documents: %s", str(e), exc_info=True)
            raise DatabaseError(f"Failed to delete documents: {str(e)}") from e

    def delete_documents_by_source(self, sources: List[str]) -> int:
        """Delete documents by source (URI)"""
        if not sources:
            logger.warning("No sources provided for deletion")
            return 0

        try:
            count = self.db.delete_documents_by_source(sources)
            logger.info("Deleted %d documents by source", count)
            return count
        except Exception as e:
            logger.error("Error deleting documents by source: %s", str(e), exc_info=True)
            raise DatabaseError(f"Failed to delete documents by source: {str(e)}") from e

