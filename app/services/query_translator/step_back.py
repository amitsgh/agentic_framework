"""Step-Back Query Translation Service"""

from typing import List

from app.services.query_translator.base import BaseQueryTranslator
from app.services.llm.base import BaseLLM
from app.utils.logger import setuplog

logger = setuplog(__name__)


class StepBackTranslator(BaseQueryTranslator):
    """Abstract query to higher-level concepts for better retrieval"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def translate(self, query: str) -> str:
        """Abstract query to step-back question"""
        try:
            prompt = f"""Given the following specific question, generate a more abstract, high-level question that would help answer it. The abstract question should focus on general concepts, principles, or background knowledge.

Specific question: {query}

Abstract step-back question:"""

            messages = [{"role": "user", "message": prompt}]
            response = self.llm.model_response(messages)

            abstract_query = response.strip()
            
            logger.info("Generated step-back abstract query")
            return abstract_query

        except Exception as e:
            logger.warning("Step-back translation failed: %s", str(e))
            return query

