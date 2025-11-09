"""Abstract Class for Embeddigns"""

from typing import List, Union
import numpy as np
from numpy.typing import NDArray
from abc import ABC, abstractmethod


class BaseEmbeddings(ABC):
    """Base class for embeddings"""

    @abstractmethod
    def embed(self, text: Union[str, List[str]]) -> NDArray[np.float32]:
        """Generate Embeddings"""

        raise NotImplementedError("Subclass must implement the embed method")
