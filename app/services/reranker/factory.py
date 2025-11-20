"""Factory for Re-ranking Services"""

from app.services.reranker.base import BaseReranker
from app.services.reranker.llm_reranker import LLMReranker
from app.services.reranker.rag_fusion_reranker import RAGFusionReranker
from app.services.llm.base import BaseLLM
from app.services.embedder.base import BaseEmbeddings
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)


def get_reranker_instance(
    reranker_type: str | None = None,
    llm: BaseLLM | None = None,
    embeddings: BaseEmbeddings | None = None,
) -> BaseReranker:
    """Get reranker instance based on type"""
    reranker_type = reranker_type or getattr(config, "RERANKER_TYPE", "llm")

    if reranker_type == "llm":
        if not llm:
            raise ValueError("LLM required for LLMReranker")
        return LLMReranker(llm)
    elif reranker_type == "rag_fusion":
        if not embeddings:
            raise ValueError("Embeddings required for RAGFusionReranker")
        return RAGFusionReranker(embeddings)
    else:
        raise ValueError(f"Unknown reranker type: {reranker_type}")

