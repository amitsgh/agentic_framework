"""Query Decomposition Translation Service"""

from typing import List

from app.services.query_translator.base import BaseQueryTranslator
from app.services.llm.base import BaseLLM
from app.utils.logger import setuplog

logger = setuplog(__name__)


class DecompositionTranslator(BaseQueryTranslator):
    """Break down complex queries into simpler sub-queries"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def translate(self, query: str) -> List[str]:
        """Decompose query into sub-queries"""
        try:
            prompt = f"""Break down the following complex query into simpler, more focused sub-queries that can be answered independently.

Complex query: {query}

Generate 2-4 sub-queries, one per line:"""

            messages = [{"role": "user", "message": prompt}]
            response = self.llm.model_response(messages)

            # Parse sub-queries
            sub_queries = self._parse_queries(response)
            
            # Always include original
            if query not in sub_queries:
                sub_queries.append(query)

            logger.info("Decomposed query into %d sub-queries", len(sub_queries))
            return sub_queries

        except Exception as e:
            logger.warning("Query decomposition failed: %s", str(e))
            return [query]

    def _parse_queries(self, response: str) -> List[str]:
        """Parse sub-queries from LLM response"""
        queries = []
        for line in response.split('\n'):
            line = line.strip()
            line = line.lstrip('0123456789.-) ')
            if line and len(line) > 10:
                queries.append(line)
        return queries

