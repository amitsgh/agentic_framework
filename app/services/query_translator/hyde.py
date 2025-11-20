"""HyDE (Hypothetical Document Embeddings) Translation Service"""

from typing import List

from app.services.query_translator.base import BaseQueryTranslator
from app.services.llm.base import BaseLLM
from app.utils.logger import setuplog

logger = setuplog(__name__)


class HyDETranslator(BaseQueryTranslator):
    """Generate hypothetical documents that would answer the query"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def translate(self, query: str) -> str:
        """Generate hypothetical document"""
        try:
            prompt = f"""Write a hypothetical document that would answer the following question. Write it as if it's a real document containing the answer.

Question: {query}

Hypothetical document:"""

            messages = [{"role": "user", "message": prompt}]
            response = self.llm.model_response(messages)

            # Use the hypothetical document as the query
            hypothetical_doc = response.strip()
            
            logger.info("Generated hypothetical document for HyDE")
            return hypothetical_doc

        except Exception as e:
            logger.warning("HyDE translation failed: %s", str(e))
            return query

