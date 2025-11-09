"""Abstract Class for Chunker"""

from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic

from app.models.document_model import Document

T = TypeVar("T")


class BaseChunker(ABC, Generic[T]):
    """Abstract class for chunker"""

    @abstractmethod
    def chunk(self, documents: List[T]) -> List[Document]:
        """Generate chunks of documents"""

        raise NotImplementedError("Subclasses must implement the chunk method")
