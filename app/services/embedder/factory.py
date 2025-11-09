"""Embeddigns Factor"""

from typing import Type

from app.services.embedder.base import BaseEmbeddings
from app.services.embedder.huggingface_embedder import HuggingFaceEmbeddigns
from app.core.config import config
from app.core.logger import setuplog

logger = setuplog(__name__)

EMBEDDINGS_REGISTRY: dict[str, Type[BaseEmbeddings]] = {
    "huggingface": HuggingFaceEmbeddigns,
    # add more parsers
}


def get_extractor_instance() -> BaseEmbeddings:
    """Get extractor instance"""

    embeddings_class = EMBEDDINGS_REGISTRY.get(config.EMBEDDINGS_TYPE)

    if embeddings_class is None:
        logger.warning(
            "Parser type %s not found, falling back to default", config.EMBEDDINGS_TYPE
        )
        embeddings_class = HuggingFaceEmbeddigns

    return embeddings_class()  # type: ignore
