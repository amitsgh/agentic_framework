"""Factory for RAPTOR Services"""

from app.services.raptor.base import BaseRaptor
from app.services.raptor.llm_raptor import LLMRaptor
from app.services.llm.base import BaseLLM
from app.services.embedder.base import BaseEmbeddings
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)


def get_raptor_instance(
    raptor_type: str | None = None,
    llm: BaseLLM | None = None,
    embeddings: BaseEmbeddings | None = None,
) -> BaseRaptor:
    """Get RAPTOR instance based on type"""
    raptor_type = raptor_type or getattr(config, "RAPTOR_TYPE", "llm")

    if not llm:
        raise ValueError("LLM required for RAPTOR")
    if not embeddings:
        raise ValueError("Embeddings required for RAPTOR")

    if raptor_type == "llm":
        return LLMRaptor(llm, embeddings)
    else:
        raise ValueError(f"Unknown RAPTOR type: {raptor_type}")

