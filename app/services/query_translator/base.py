"""Abstract Class for Query Translation Services"""

from abc import ABC, abstractmethod
from typing import List


class BaseQueryTranslator(ABC):
    """Abstract base class for query translation/transformation"""

    @abstractmethod
    def translate(self, query: str) -> str | List[str]:
        """
        Translate/transform query for better retrieval
        
        Args:
            query: Original query
            
        Returns:
            Translated query (single string) or multiple query variations (list)
        """
        raise NotImplementedError("translate must be implemented in subclass")

