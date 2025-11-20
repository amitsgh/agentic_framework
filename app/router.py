"""Central Router Registration"""

from fastapi import FastAPI

from app.api.v1.documents import router as document_router
from app.api.v1.chat import router as chat_router
from app.api.v1.graph import router as graph_router


def register_routers(app: FastAPI):
    """Register all routes to FastAPI application"""

    app.include_router(document_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(graph_router, prefix="/api/v1")
