"""LLM Factory"""

from typing import Type

from app.services.llm.base import BaseLLM
from app.services.llm.ollama_llm import OllamaModel
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)

LLM_REGISTRY: dict[str, Type[BaseLLM]] = {
    "ollama": OllamaModel,
    # add more llms
}


def get_llm_instance(model_name: str) -> BaseLLM:
    """Get llm instance"""

    if "/" in model_name:
        provider, model = model_name.split("/", 1)
    else:
        provider = config.LLM_TYPE.lower()
        model = model_name

    llm_class = LLM_REGISTRY.get(provider)

    if llm_class is None:
        logger.warning(
            "LLM type %s not found, falling back to default", config.LLM_TYPE
        )
        llm_class = OllamaModel

    return llm_class(model)  # type: ignore
