"""FastAPI Application"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.dependency import get_embeddings, get_extractor, get_cache
from app.router import register_routers
from app.config import config
from app.exceptions.error_handler import (
    framework_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
)

from app.exceptions.base import FrameworkException
from app.logger import setuplog

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
        logger.debug("Validating embeddings service...")
        embeddings = get_embeddings()
        logger.info("Embeddings service initialized successfully")

        logger.debug("Validating extractor service...")
        extractor = get_extractor()
        logger.info("Extractor service initialized successfully")

        logger.debug("Validating cache service...")
        cache = get_cache()
        if cache:
            logger.info("Cache service initialized successfully")
        else:
            logger.warning("Cache service is disabled or unavailable")

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

app.add_exception_handler(
    FrameworkException,
    framework_exception_handler,  # pyright: ignore[reportArgumentType]
)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,  # pyright: ignore[reportArgumentType]
)
app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,  # pyright: ignore[reportArgumentType]
)
app.add_exception_handler(Exception, general_exception_handler)

register_routers(app)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"message": "LLM Application", "status": "healty", "version": "1.0.0"}
