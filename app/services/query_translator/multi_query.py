"""Multi-Query Translation Service"""

from typing import List

from app.services.query_translator.base import BaseQueryTranslator
from app.services.llm.base import BaseLLM
from app.utils.logger import setuplog

logger = setuplog(__name__)


class MultiQueryTranslator(BaseQueryTranslator):
    """Generate multiple query variations for better retrieval"""

    def __init__(self, llm: BaseLLM, num_queries: int = 3):
        self.llm = llm
        self.num_queries = num_queries

    def translate(self, query: str) -> List[str]:
        """Generate multiple query variations"""
        try:
            prompt = f"""Generate {self.num_queries} different versions of the following query. Each version should be a distinct way of asking the same question, using different wording, focus, or perspective.

Original query: {query}

Generate {self.num_queries} variations, one per line:"""

            messages = [{"role": "user", "message": prompt}]
            response = self.llm.model_response(messages)

            # Parse queries from response
            queries = self._parse_queries(response)
            
            # Always include original query
            if query not in queries:
                queries.insert(0, query)

            logger.info("Generated %d query variations", len(queries))
            return queries[:self.num_queries + 1]  # +1 for original

        except Exception as e:
            logger.warning("Multi-query translation failed: %s", str(e))
            return [query]

    def _parse_queries(self, response: str) -> List[str]:
        """Parse multiple queries from LLM response"""
        queries = []
        for line in response.split('\n'):
            line = line.strip()
            # Remove numbering if present
            line = line.lstrip('0123456789.-) ')
            if line and len(line) > 10:  # Filter out very short lines
                queries.append(line)
        return queries

