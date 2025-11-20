"""Abstract Class for Document Refinement Services"""

from abc import ABC, abstractmethod
from typing import List

from app.models.document_model import Document


class BaseRefiner(ABC):
    """Abstract base class for document refinement (CRAG)"""

    @abstractmethod
    def refine(
        self, query: str, documents: List[Document]
    ) -> tuple[List[Document], bool]:
        """
        Refine documents using CRAG (Critique and Revise Augmented Generation)
        
        Args:
            query: The search query
            documents: List of documents to refine
            
        Returns:
            Tuple of (refined_documents, needs_retrieval)
            - refined_documents: Refined/revised documents
            - needs_retrieval: Boolean indicating if new retrieval is needed
        """
        raise NotImplementedError("refine must be implemented in subclass")

