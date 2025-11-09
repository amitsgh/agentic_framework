"""Singleton Embeddings Class"""

from typing import List, Union
import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from app.services.embedder.base import BaseEmbeddings


class HuggingFaceEmbeddigns(BaseEmbeddings):
    """Hugging Face embeddigns class"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: Union[str, List[str]]) -> NDArray[np.float32]:
        """Generate embeddigs"""

        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(texts, convert_to_tensor=False)  # type: ignore
        return np.array(embeddings, dtype=np.float32)
