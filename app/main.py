"""FastAPI Application"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependency import (
    get_embeddings,
    get_extractor,
    get_cache,
    get_storage,
    get_chunker,
    get_llm,
    get_db_sync,
)
from app.router import register_routers
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)

logger.info("Starting Agentic Framework API application...")
logger.debug(
    "Application configuration loaded: LLM_TYPE=%s, DATABASE_TYPE=%s",
    config.LLM_TYPE,
    config.DATABASE_TYPE,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup event triggered.")
    logger.debug("Initializing application dependencies...")

    try:
        # Core document processing services
        logger.debug("Validating embeddings service...")
        _ = get_embeddings()  # Validate service initialization
        logger.info("Embeddings service initialized successfully")

        logger.debug("Validating extractor service...")
        _ = get_extractor()  # Validate service initialization
        logger.info("Extractor service initialized successfully")

        logger.debug("Validating chunker service...")
        _ = get_chunker()  # Validate service initialization
        logger.info("Chunker service initialized successfully")

        # Storage services
        logger.debug("Validating MinIO storage service...")
        _ = get_storage()  # Validate service initialization
        logger.info("MinIO storage service initialized successfully")

        # Cache service (optional)
        logger.debug("Validating cache service...")
        cache = get_cache()
        if cache:
            logger.info("Cache service initialized successfully")
        else:
            logger.warning("Cache service is disabled or unavailable")

        # Database service (for vector storage)
        logger.debug("Validating database service...")
        db_gen = get_db_sync()
        db = next(db_gen)
        try:
            logger.info("Database service initialized successfully")
        finally:
            db.disconnect()

        # LLM service (critical for chat)
        logger.debug("Validating LLM service...")
        _ = get_llm()  # Validate service initialization
        logger.info("LLM service initialized successfully")

        logger.info("All critical services validated during startup")

    except Exception as e:
        logger.critical(
            "Failed to initialize critical services during startup: %s",
            str(e),
            exc_info=True,
        )
        raise

    yield

    logger.info("Application shutdown event triggered.")
    logger.debug("Cleaning up application resources...")


app = FastAPI(
    title="Agentic Framework API",
    description="LLM Application with RAG capabilities",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routers(app)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"message": "LLM Application", "status": "healty", "version": "1.0.0"}
