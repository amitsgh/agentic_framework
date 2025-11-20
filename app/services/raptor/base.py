"""Abstract Class for RAPTOR (Hierarchical Indexing) Services"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from app.models.document_model import Document


class BaseRaptor(ABC):
    """Abstract base class for RAPTOR hierarchical indexing"""

    @abstractmethod
    def build_hierarchy(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Build hierarchical tree structure from documents
        
        Args:
            documents: List of documents to organize
            
        Returns:
            Dictionary representing hierarchical structure with:
                - clusters: Grouped documents
                - summaries: Summaries at different levels
                - tree: Tree structure
        """
        raise NotImplementedError("build_hierarchy must be implemented in subclass")

    @abstractmethod
    def query_hierarchy(
        self, query: str, hierarchy: Dict[str, Any]
    ) -> List[Document]:
        """
        Query hierarchical structure for relevant documents
        
        Args:
            query: Search query
            hierarchy: Hierarchical structure from build_hierarchy
            
        Returns:
            List of relevant documents from hierarchy
        """
        raise NotImplementedError("query_hierarchy must be implemented in subclass")

