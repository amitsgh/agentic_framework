# app/dependency.py
"""Dependency Management"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator, Optional

from app.services.cache.base import BaseCache
from app.services.embedder.factory import get_embeddings_instance
from app.services.db.factory import get_db_instance
from app.services.extractor.factory import get_extractor_instance
from app.services.chunker.factor import get_chunker_instance
from app.services.llm.factory import get_llm_instance
from app.services.cache.factor import get_cache_instance
from app.services.db.base import BaseDB
from app.services.embedder.base import BaseEmbeddings
from app.services.extractor.base import BaseExtractor
from app.services.chunker.base import BaseChunker
from app.services.llm.base import BaseLLM
from app.services.cache.base import BaseCache
from app.core.logger import setuplog
from app.core.config import config

logger = setuplog(__name__)


_embeddings_instance: BaseEmbeddings | None = None
_extractor_instance: BaseExtractor | None = None
_cache_instance: BaseCache | None = None  # Add singleton cache


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


def get_cache() -> Optional[BaseCache]:
    """Get cache instance (singleton, independent of DB lifecycle)"""

    global _cache_instance

    # Return None if caching is disabled
    if not config.ENABLE_CACHING:
        return None

    if _cache_instance is None:
        try:

            _cache_instance = get_cache_instance()
            logger.info("Standalone cache instance initialized (singleton)")

        except Exception as e:
            logger.error("Failed to initialize cache: %s", str(e), exc_info=True)
            return None

    return _cache_instance
