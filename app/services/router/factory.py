"""Factory for Routing Services"""

from app.services.router.base import BaseRouter
from app.services.router.llm_router import LLMRouter
from app.services.router.semantic_router import SemanticRouter
from app.services.llm.base import BaseLLM
from app.services.embedder.base import BaseEmbeddings
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)


def get_router_instance(
    router_type: str | None = None,
    llm: BaseLLM | None = None,
    embeddings: BaseEmbeddings | None = None,
) -> BaseRouter:
    """Get router instance based on type"""
    router_type = router_type or getattr(config, "ROUTER_TYPE", "llm")

    if router_type == "llm":
        if not llm:
            raise ValueError("LLM required for LLMRouter")
        return LLMRouter(llm)
    elif router_type == "semantic":
        if not embeddings:
            raise ValueError("Embeddings required for SemanticRouter")
        return SemanticRouter(embeddings)
    else:
        raise ValueError(f"Unknown router type: {router_type}")

