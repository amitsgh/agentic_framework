"""Extractor Factor"""

from typing import Type

from app.services.extractor.base import BaseExtractor
from app.services.extractor.docling_extractor import DoclingExtractor
from app.config import config
from app.logger import setuplog

logger = setuplog(__name__)

EXTRACTOR_REGISTRY: dict[str, Type[BaseExtractor]] = {
    "docling": DoclingExtractor,
    # add more parsers
}


def get_extractor_instance() -> BaseExtractor:
    """Get extractor instance"""

    extractor_class = EXTRACTOR_REGISTRY.get(config.EXTRACTOR_TYPE)

    if extractor_class is None:
        logger.warning(
            "Parser type %s not found, falling back to default", config.EXTRACTOR_TYPE
        )
        extractor_class = DoclingExtractor

    return extractor_class()  # type: ignore
