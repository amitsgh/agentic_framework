"""LLM-based Logical Routing Service"""

from typing import Dict, Any

from app.services.router.base import BaseRouter, RouteTarget
from app.services.llm.base import BaseLLM
from app.utils.logger import setuplog

logger = setuplog(__name__)


class LLMRouter(BaseRouter):
    """Logical routing using LLM to decide data source"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def route(self, query: str) -> Dict[str, Any]:
        """Route query to appropriate data source using LLM"""
        try:
            prompt = f"""Analyze the following query and determine which database type would be most appropriate for answering it.

Query: {query}

Available options:
1. vector_db - For semantic similarity search, general knowledge, document retrieval
2. graph_db - For relationship queries, entity connections, network analysis
3. relational_db - For structured data, SQL queries, tabular information
4. multi - For queries that need multiple data sources

Respond with only the option number or name (e.g., "vector_db" or "1"):"""

            messages = [{"role": "user", "message": prompt}]
            response = self.llm.model_response(messages).strip().lower()

            # Parse response
            target = self._parse_target(response)
            
            logger.info("Routed query to: %s", target.value)
            return {
                "target": target,
                "strategy": "logical",
                "metadata": {"reasoning": response}
            }

        except Exception as e:
            logger.warning("Routing failed: %s, defaulting to vector_db", str(e))
            return {
                "target": RouteTarget.VECTOR_DB,
                "strategy": "default",
                "metadata": {}
            }

    def _parse_target(self, response: str) -> RouteTarget:
        """Parse routing target from LLM response"""
        response_lower = response.lower()
        
        if "graph" in response_lower or "2" in response:
            return RouteTarget.GRAPH_DB
        elif "relational" in response_lower or "sql" in response_lower or "3" in response:
            return RouteTarget.RELATIONAL_DB
        elif "multi" in response_lower or "4" in response:
            return RouteTarget.MULTI
        else:
            return RouteTarget.VECTOR_DB

