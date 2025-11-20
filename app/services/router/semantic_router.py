"""Semantic Routing Service"""

from typing import Dict, Any, List

from app.services.router.base import BaseRouter, RouteTarget
from app.services.embedder.base import BaseEmbeddings
from app.utils.logger import setuplog

logger = setuplog(__name__)


class SemanticRouter(BaseRouter):
    """Semantic routing based on query embedding similarity to prompt templates"""

    def __init__(
        self,
        embeddings: BaseEmbeddings,
        prompt_templates: List[Dict[str, str]] | None = None,
    ):
        self.embeddings = embeddings
        self.prompt_templates = prompt_templates or self._default_templates()

    def route(self, query: str) -> Dict[str, Any]:
        """Route query based on semantic similarity to prompt templates"""
        try:
            query_embedding = self.embeddings.embed(query)
            
            best_match = None
            best_score = -1.0
            
            for template in self.prompt_templates:
                template_embedding = self.embeddings.embed(template["prompt"])
                
                # Cosine similarity
                import numpy as np
                similarity = np.dot(query_embedding, template_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(template_embedding)
                )
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = template

            target = RouteTarget(best_match["target"]) if best_match else RouteTarget.VECTOR_DB
            
            logger.info("Semantically routed query to: %s (score: %.3f)", target.value, best_score)
            return {
                "target": target,
                "strategy": "semantic",
                "metadata": {
                    "similarity_score": best_score,
                    "matched_template": best_match["name"] if best_match else None
                }
            }

        except Exception as e:
            logger.warning("Semantic routing failed: %s", str(e))
            return {
                "target": RouteTarget.VECTOR_DB,
                "strategy": "default",
                "metadata": {}
            }

    def _default_templates(self) -> List[Dict[str, str]]:
        """Default prompt templates for routing"""
        return [
            {
                "name": "vector_search",
                "prompt": "Find documents similar to this query using semantic search",
                "target": RouteTarget.VECTOR_DB.value
            },
            {
                "name": "graph_relations",
                "prompt": "Find relationships and connections between entities",
                "target": RouteTarget.GRAPH_DB.value
            },
            {
                "name": "structured_data",
                "prompt": "Query structured data using SQL or relational queries",
                "target": RouteTarget.RELATIONAL_DB.value
            }
        ]

