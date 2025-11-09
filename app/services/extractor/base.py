"""Abstract Class for Extractor"""

from abc import ABC, abstractmethod
from typing import List, Union

from docling_core.types.doc.document import DoclingDocument

from app.models.document_model import Document


class BaseExtractor(ABC):
    """Abstract base class for extractor"""

    @abstractmethod
    def supported_extension(self) -> List[str]:
        """Returns a list of file extension parser can handle"""

    @abstractmethod
    def extract(
        self, data: Union[str, List[str]]
    ) -> Union[List[Document], List[DoclingDocument]]:
        """Extract input data and return structured output"""
