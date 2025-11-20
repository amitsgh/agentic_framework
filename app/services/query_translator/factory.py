"""Factory for Query Translation Services"""

from app.services.query_translator.base import BaseQueryTranslator
from app.services.query_translator.multi_query import MultiQueryTranslator
from app.services.query_translator.decomposition import DecompositionTranslator
from app.services.query_translator.hyde import HyDETranslator
from app.services.query_translator.step_back import StepBackTranslator
from app.services.llm.base import BaseLLM
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)


def get_query_translator_instance(
    translator_type: str | None = None,
    llm: BaseLLM | None = None,
) -> BaseQueryTranslator:
    """Get query translator instance based on type"""
    translator_type = translator_type or getattr(config, "QUERY_TRANSLATOR_TYPE", "multi_query")

    if not llm:
        raise ValueError("LLM required for query translators")

    if translator_type == "multi_query":
        return MultiQueryTranslator(llm)
    elif translator_type == "decomposition":
        return DecompositionTranslator(llm)
    elif translator_type == "hyde":
        return HyDETranslator(llm)
    elif translator_type == "step_back":
        return StepBackTranslator(llm)
    else:
        raise ValueError(f"Unknown query translator type: {translator_type}")

