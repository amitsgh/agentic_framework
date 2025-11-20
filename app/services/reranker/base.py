"""Abstract Class for Re-ranking Services"""

from abc import ABC, abstractmethod
from typing import List

from app.models.document_model import Document


class BaseReranker(ABC):
    """Abstract base class for document re-ranking"""

    @abstractmethod
    def rerank(
        self, query: str, documents: List[Document], top_k: int | None = None
    ) -> List[Document]:
        """
        Re-rank documents based on relevance to query
        
        Args:
            query: The search query
            documents: List of documents to re-rank
            top_k: Optional limit on number of documents to return
            
        Returns:
            Re-ranked list of documents
        """
        raise NotImplementedError("rerank must be implemented in subclass")

