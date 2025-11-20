"""Factory for Refinement Services"""

from app.services.refiner.base import BaseRefiner
from app.services.refiner.crag_refiner import CRAGRefiner
from app.services.llm.base import BaseLLM
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)


def get_refiner_instance(
    refiner_type: str | None = None,
    llm: BaseLLM | None = None,
) -> BaseRefiner:
    """Get refiner instance based on type"""
    refiner_type = refiner_type or getattr(config, "REFINER_TYPE", "crag")

    if not llm:
        raise ValueError("LLM required for refiners")

    if refiner_type == "crag":
        return CRAGRefiner(llm)
    else:
        raise ValueError(f"Unknown refiner type: {refiner_type}")

