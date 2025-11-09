"""Embeddigns Factor"""

from typing import Type

from app.services.chunker.base import BaseChunker
from app.services.chunker.hybrid_chunker import DoclingHybridChunker
from app.core.config import config
from app.core.logger import setuplog

logger = setuplog(__name__)

CHUNKER_REGISTRY: dict[str, Type[BaseChunker]] = {
    "docling-hybrid": DoclingHybridChunker,
    # add more parsers
}


def get_chunker_instance() -> BaseChunker:
    """Get chunker instance"""

    chunker_class = CHUNKER_REGISTRY.get(config.CHUNKER_TYPER)

    if chunker_class is None:
        logger.warning(
            "Parser type %s not found, falling back to default", config.CHUNKER_TYPER
        )
        chunker_class = DoclingHybridChunker

    return chunker_class(config.MODEL_NAME)  # type: ignore
