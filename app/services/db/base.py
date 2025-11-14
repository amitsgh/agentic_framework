"""Abstract Class for Database Services"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from app.services.embedder.base import BaseEmbeddings
from app.models.document_model import Document


class BaseDB(ABC):
    """Abstract base class for all db services"""

    @abstractmethod
    def connect(self) -> None:
        """Connect to databse"""

        raise NotImplementedError("Subclass must implement the connect method")

    @abstractmethod
    def get_client(self) -> Any:
        """Get db client"""

        raise NotImplementedError("Subclas must implement the get_cleint method")

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from database"""

        raise NotImplementedError("Subclass must implement the disconnect method")

    @abstractmethod
    def add_documents(
        self, data: List[Document], embeddings: BaseEmbeddings
    ) -> List[str]:
        """Ingest data to database"""

        raise NotImplementedError("Subclass must implement the add_document method")

    @abstractmethod
    def similarity_search(
        self, query: str, embeddings: BaseEmbeddings, top_k: int = 5
    ) -> List[Document]:
        """Search documents using similarity search"""

        raise NotImplementedError(
            "Subclass must implement the similarity_search method"
        )

    # @abstractmethod
    # def delete_documents_by_id(self, document_ids: List[str]) -> bool:
    #     """Delete a document by ID"""

    #     raise NotImplementedError(
    #         "Subclass must implement the delete_documents_by_id method"
    #     )

    @abstractmethod
    def delete_documents_by_source(self, sources: List[str]) -> int:
        """Delete a document by Source (URI)"""

        raise NotImplementedError(
            "Subclass must implement the delete_documents_by_source method"
        )

    @abstractmethod
    def delete_all(self) -> int:
        """Delete all documents from the database"""

        raise NotImplementedError("Subclass must implement the delete_all method")
