"""LLM Factory"""

from typing import Type

from app.services.llm.base import BaseLLM
from app.services.llm.ollama_llm import OllamaModel
from app.core.config import config

from app.core.logger import setuplog

logger = setuplog(__name__)

LLM_REGISTRY: dict[str, Type[BaseLLM]] = {
    "ollama": OllamaModel,
    # add more llms
}

def get_llm_instance(model_name: str) -> BaseLLM:
    """Get llm instance"""
    
    llm, model = model_name.split('/')
 
    llm_class = LLM_REGISTRY.get(llm or config.LLM_TYPE.lower())

    if llm_class is None:
        logger.warning(
            "LLM type %s not found, falling back to default", config.LLM_TYPE
        )
        llm_class = OllamaModel
        
    return llm_class(model) # type: ignore 
