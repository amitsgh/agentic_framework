"""Abstract Class for Routing Services"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any


class RouteTarget(str, Enum):
    """Available routing targets"""
    VECTOR_DB = "vector_db"
    GRAPH_DB = "graph_db"
    RELATIONAL_DB = "relational_db"
    MULTI = "multi"  # Route to multiple sources


class BaseRouter(ABC):
    """Abstract base class for query routing"""

    @abstractmethod
    def route(self, query: str) -> Dict[str, Any]:
        """
        Route query to appropriate data source(s)
        
        Args:
            query: The search query
            
        Returns:
            Dictionary with:
                - target: RouteTarget enum
                - strategy: Optional routing strategy
                - metadata: Additional routing metadata
        """
        raise NotImplementedError("route must be implemented in subclass")

