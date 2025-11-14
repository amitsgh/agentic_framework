"""FastAPI Application"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.router import register_routers
from app.core.config import config
from app.core.exceptions.error_handler import (
    framework_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
)

from app.core.exceptions.base import FrameworkException
from app.core.logger import setuplog

logger = setuplog(__name__)

logger.info("Starting Agentic Framework API application...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup event triggered.")
    yield  # <-- Application runs while paused here
    logger.info("Application shutdown event triggered.")


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

# @app.get("/")
# async def root():
#     """Root endpoint"""
#     return {"message": "LLM Application", "status": "healty", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"message": "LLM Application", "status": "healty", "version": "1.0.0"}
