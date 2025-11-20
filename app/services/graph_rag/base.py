"""Abstract Class for Graph RAG Services"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from app.models.document_model import Document


class BaseGraphRAG(ABC):
    """Abstract base class for Graph RAG operations"""

    @abstractmethod
    def text_to_cypher(self, query: str) -> str:
        """
        Convert natural language query to Cypher query
        
        Args:
            query: Natural language query
            
        Returns:
            Cypher query string
        """
        raise NotImplementedError("text_to_cypher must be implemented in subclass")

    @abstractmethod
    def execute_cypher(self, cypher_query: str) -> List[Dict[str, Any]]:
        """
        Execute Cypher query and return results
        
        Args:
            cypher_query: Cypher query string
            
        Returns:
            List of result dictionaries
        """
        raise NotImplementedError("execute_cypher must be implemented in subclass")

    @abstractmethod
    def query(self, query: str) -> List[Document]:
        """
        Query graph database using natural language
        
        Args:
            query: Natural language query
            
        Returns:
            List of Document objects from graph results
        """
        raise NotImplementedError("query must be implemented in subclass")

