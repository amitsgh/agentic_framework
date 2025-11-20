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
from app.utils.logger import setuplog
from app.config import config
from app.services.storage.minio_storage import MinIOStorage
from app.services.reranker.factory import get_reranker_instance
from app.services.query_translator.factory import get_query_translator_instance
from app.services.router.factory import get_router_instance
from app.services.refiner.factory import get_refiner_instance
from app.services.graph_rag.factory import get_graph_rag_instance
from app.services.raptor.factory import get_raptor_instance
from app.services.reranker.base import BaseReranker
from app.services.query_translator.base import BaseQueryTranslator
from app.services.router.base import BaseRouter
from app.services.refiner.base import BaseRefiner
from app.services.graph_rag.base import BaseGraphRAG
from app.services.raptor.base import BaseRaptor

logger = setuplog(__name__)

_storage_instance: Optional[MinIOStorage] = None

def get_storage() -> MinIOStorage:
    """Get MinIO storage instance (singleton)"""
    global _storage_instance
    if _storage_instance is None:
        logger.info("Initializing MinIO storage (singleton)")
        try:
            _storage_instance = MinIOStorage()
            logger.debug("MinIO storage instance created successfully")
        except Exception as e:
            logger.critical("Failed to initialize MinIO storage: %s", str(e), exc_info=True)
            raise
    return _storage_instance


_embeddings_instance: BaseEmbeddings | None = None
_extractor_instance: BaseExtractor | None = None
_cache_instance: BaseCache | None = None  # Add singleton cache


def get_embeddings() -> BaseEmbeddings:
    """Get embeddings instance (singleton)"""

    global _embeddings_instance
    if _embeddings_instance is None:
        logger.info("Initializing embeddings model (singleton)")
        logger.debug("Embeddings type: %s, Model: %s", config.EMBEDDINGS_TYPE, config.MODEL_NAME)
        try:
            _embeddings_instance = get_embeddings_instance()
            logger.debug("Embeddings instance created successfully")
        except Exception as e:
            logger.critical("Failed to initialize embeddings service: %s", str(e), exc_info=True)
            raise
    else:
        logger.debug("Returning existing embeddings singleton instance")
    return _embeddings_instance


def get_extractor() -> BaseExtractor:
    """Get extractor instance (singleton)"""

    global _extractor_instance
    if _extractor_instance is None:
        logger.info("Initializing extractor (singleton)")
        logger.debug("Extractor type: %s", config.EXTRACTOR_TYPE)
        try:
            _extractor_instance = get_extractor_instance()
            logger.debug("Extractor instance created successfully")
        except Exception as e:
            logger.critical("Failed to initialize extractor service: %s", str(e), exc_info=True)
            raise
    else:
        logger.debug("Returning existing extractor singleton instance")
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
    logger.debug("Getting database instance: %s", config.DATABASE_TYPE)
    try:
        db.connect()
        logger.info("Database connection established")
        logger.debug("Database connection successful for type: %s", config.DATABASE_TYPE)
        yield db

    except Exception as e:
        logger.critical("Database connection failed: %s", str(e), exc_info=True)
        raise
    finally:
        db.disconnect()
        logger.info("Database connection closed")
        logger.debug("Database cleanup completed")


def get_db_sync() -> Generator[BaseDB, None, None]:
    """Get database instance with lifecycle management (sync)"""

    db = get_db_instance()
    logger.debug("Getting database instance (sync): %s", config.DATABASE_TYPE)
    try:
        db.connect()
        logger.info("Database connection established")
        logger.debug("Database connection successful for type: %s", config.DATABASE_TYPE)
        yield db

    except Exception as e:
        logger.critical("Database connection failed: %s", str(e), exc_info=True)
        raise
    finally:
        db.disconnect()
        logger.info("Database connection closed")
        logger.debug("Database cleanup completed")


def get_cache() -> Optional[BaseCache]:
    """Get cache instance (singleton, independent of DB lifecycle)"""

    global _cache_instance

    # Return None if caching is disabled
    if not config.ENABLE_CACHING:
        logger.debug("Caching is disabled in configuration")
        return None

    if _cache_instance is None:
        logger.debug("Initializing cache instance: %s", config.CACHE_TYPE)
        try:
            _cache_instance = get_cache_instance()
            logger.info("Standalone cache instance initialized (singleton)")
            logger.debug("Cache instance created successfully")

        except Exception as e:
            logger.warning("Failed to initialize cache service: %s", str(e), exc_info=True)
            # Don't raise - cache is optional, but log as warning
            return None
    else:
        logger.debug("Returning existing cache singleton instance")

    return _cache_instance


# Advanced RAG Services (optional, lazy-loaded)
_reranker_instance: Optional[BaseReranker] = None
_query_translator_instance: Optional[BaseQueryTranslator] = None
_router_instance: Optional[BaseRouter] = None
_refiner_instance: Optional[BaseRefiner] = None
_graph_rag_instance: Optional[BaseGraphRAG] = None
_raptor_instance: Optional[BaseRaptor] = None


def get_reranker() -> Optional[BaseReranker]:
    """Get reranker instance (optional)"""
    global _reranker_instance
    if not config.ENABLE_RERANKING:
        return None
    
    if _reranker_instance is None:
        try:
            llm = get_llm()
            embeddings = get_embeddings()
            _reranker_instance = get_reranker_instance(
                reranker_type=config.RERANKER_TYPE,
                llm=llm if config.RERANKER_TYPE == "llm" else None,
                embeddings=embeddings if config.RERANKER_TYPE == "rag_fusion" else None,
            )
        except Exception as e:
            logger.warning("Failed to initialize reranker: %s", str(e))
            return None
    return _reranker_instance


def get_query_translator() -> Optional[BaseQueryTranslator]:
    """Get query translator instance (optional)"""
    global _query_translator_instance
    if not config.ENABLE_QUERY_TRANSLATION:
        return None
    
    if _query_translator_instance is None:
        try:
            llm = get_llm()
            _query_translator_instance = get_query_translator_instance(
                translator_type=config.QUERY_TRANSLATOR_TYPE,
                llm=llm,
            )
        except Exception as e:
            logger.warning("Failed to initialize query translator: %s", str(e))
            return None
    return _query_translator_instance


def get_router() -> Optional[BaseRouter]:
    """Get router instance (optional)"""
    global _router_instance
    if not config.ENABLE_ROUTING:
        return None
    
    if _router_instance is None:
        try:
            llm = get_llm()
            embeddings = get_embeddings()
            _router_instance = get_router_instance(
                router_type=config.ROUTER_TYPE,
                llm=llm if config.ROUTER_TYPE == "llm" else None,
                embeddings=embeddings if config.ROUTER_TYPE == "semantic" else None,
            )
        except Exception as e:
            logger.warning("Failed to initialize router: %s", str(e))
            return None
    return _router_instance


def get_refiner() -> Optional[BaseRefiner]:
    """Get refiner instance (optional)"""
    global _refiner_instance
    if not config.ENABLE_REFINEMENT:
        return None
    
    if _refiner_instance is None:
        try:
            llm = get_llm()
            _refiner_instance = get_refiner_instance(
                refiner_type=config.REFINER_TYPE,
                llm=llm,
            )
        except Exception as e:
            logger.warning("Failed to initialize refiner: %s", str(e))
            return None
    return _refiner_instance


def get_graph_rag() -> Optional[BaseGraphRAG]:
    """Get graph RAG instance (optional)"""
    global _graph_rag_instance
    if not config.ENABLE_GRAPH_RAG:
        return None
    
    if _graph_rag_instance is None:
        try:
            llm = get_llm()
            _graph_rag_instance = get_graph_rag_instance(
                graph_rag_type=config.GRAPH_RAG_TYPE,
                llm=llm,
                uri=config.NEO4J_URI,
                user=config.NEO4J_USER,
                password=config.NEO4J_PASSWORD,
                database=config.NEO4J_DATABASE,
            )
        except Exception as e:
            logger.warning("Failed to initialize graph RAG: %s", str(e))
            return None
    return _graph_rag_instance


def get_raptor() -> Optional[BaseRaptor]:
    """Get RAPTOR instance (optional)"""
    global _raptor_instance
    if not config.ENABLE_RAPTOR:
        return None
    
    if _raptor_instance is None:
        try:
            llm = get_llm()
            embeddings = get_embeddings()
            _raptor_instance = get_raptor_instance(
                raptor_type=config.RAPTOR_TYPE,
                llm=llm,
                embeddings=embeddings,
            )
        except Exception as e:
            logger.warning("Failed to initialize RAPTOR: %s", str(e))
            return None
    return _raptor_instance
