"""Global Error handler"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions.base import FrameworkException
from app.core.logger import setuplog

logger = setuplog(__name__)


async def framework_exception_handler(req: Request, exc: FrameworkException):
    """Handle framework exception"""

    logger.error("Framework error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Framework Error", "message": str(exc), "path": req.url.path},
    )


async def validation_exception_handler(req: Request, exc: RequestValidationError):
    """Handle validation errors"""

    logger.warning("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "path": req.url.path,
        },
    )


async def http_exception_handler(req: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Error", "message": exc.detail, "path": req.url.path},
    )


async def general_exception_handler(req: Request, exc: Exception):
    """Handle unexpected exceptions"""

    logger.exception("Unexpected error: %d", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "path": req.url.path,
        },
    )
