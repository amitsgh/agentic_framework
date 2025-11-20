"""Factory for Graph RAG Services"""

from app.services.graph_rag.base import BaseGraphRAG
from app.services.graph_rag.llm_graph_rag import LLMGraphRAG
from app.services.llm.base import BaseLLM
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)


def get_graph_rag_instance(
    graph_rag_type: str | None = None,
    llm: BaseLLM | None = None,
    uri: str | None = None,
    user: str | None = None,
    password: str | None = None,
    database: str | None = None,
) -> BaseGraphRAG:
    """Get graph RAG instance based on type"""
    graph_rag_type = graph_rag_type or getattr(config, "GRAPH_RAG_TYPE", "llm")

    if not llm:
        raise ValueError("LLM required for Graph RAG")

    if graph_rag_type == "llm":
        return LLMGraphRAG(
            llm=llm,
            uri=uri,
            user=user,
            password=password,
            database=database,
        )
    else:
        raise ValueError(f"Unknown graph RAG type: {graph_rag_type}")

