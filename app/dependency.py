"""Dependency Management"""

from app.services.embedding.huggingface_embeddings import HuggingFaceEmbeddigns


def get_embeddings():
    """Return Embeddings Class"""

    return HuggingFaceEmbeddigns()
