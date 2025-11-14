"""Dependency Management"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

from app.services.embedder.factory import get_embeddings_instance
from app.services.db.factory import get_db_instance
from app.services.extractor.factory import get_extractor_instance
from app.services.chunker.factor import get_chunker_instance
from app.services.llm.factory import get_llm_instance
from app.services.db.base import BaseDB
from app.services.embedder.base import BaseEmbeddings
from app.services.extractor.base import BaseExtractor
from app.services.chunker.base import BaseChunker
from app.services.llm.base import BaseLLM
from app.core.logger import setuplog

logger = setuplog(__name__)


_embeddings_instance: BaseEmbeddings | None = None
_extractor_instance: BaseExtractor | None = None


def get_embeddings() -> BaseEmbeddings:
    """Get embeddings instance (singleton)"""

    global _embeddings_instance
    if _embeddings_instance is None:
        logger.info("Initializing embeddings model (singleton)")
        _embeddings_instance = get_embeddings_instance()
    return _embeddings_instance


def get_extractor() -> BaseExtractor:
    """Get extractor instance (singleton)"""

    global _extractor_instance
    if _extractor_instance is None:
        logger.info("Initializing extractor (singleton)")
        _extractor_instance = get_extractor_instance()
    return _extractor_instance


def get_chunker() -> BaseChunker:
    """Get chunker instance"""

    return get_chunker_instance()


def get_llm(model_name: str = "ollama/llama2") -> BaseLLM:
    """Get LLM instance"""

    llm = get_llm_instance(model_name)
    llm.load_model()
    return llm


@asynccontextmanager
async def get_db() -> AsyncGenerator[BaseDB, None]:
    """Get database instance with lifecycle management"""

    db = get_db_instance()
    try:
        db.connect()
        logger.info("Database connection established")
        yield db

    finally:
        db.disconnect()
        logger.info("Database connection closed")


def get_db_sync() -> Generator[BaseDB, None, None]:
    """Get database instance with lifecycle management (sync)"""

    db = get_db_instance()
    try:
        db.connect()
        logger.info("Database connection established")
        yield db

    finally:
        db.disconnect()
        logger.info("Database connection closed")
