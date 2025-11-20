"""LLM-based Re-ranking Service"""

from typing import List

from app.models.document_model import Document
from app.services.reranker.base import BaseReranker
from app.services.llm.base import BaseLLM
from app.utils.logger import setuplog

logger = setuplog(__name__)


class LLMReranker(BaseReranker):
    """Re-ranker using LLM for relevance scoring (RankGPT-style)"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def rerank(
        self, query: str, documents: List[Document], top_k: int | None = None
    ) -> List[Document]:
        """Re-rank documents using LLM-based relevance scoring"""
        if not documents:
            return []

        if len(documents) == 1:
            return documents

        try:
            # Build prompt for LLM to rank documents
            doc_texts = [
                f"[{i}] {doc.content[:500]}" for i, doc in enumerate(documents)
            ]
            prompt = f"""Rank the following documents by relevance to the query. Return only the indices in order of relevance (most relevant first).

Query: {query}

Documents:
{chr(10).join(doc_texts)}

Return the ranked indices as a comma-separated list (e.g., "2,0,1"):"""

            messages = [{"role": "user", "message": prompt}]
            response = self.llm.model_response(messages)

            # Parse LLM response to get ranked indices
            ranked_indices = self._parse_ranked_indices(response, len(documents))
            
            # Re-order documents based on ranking
            reranked = [documents[i] for i in ranked_indices if i < len(documents)]
            
            # Apply top_k if specified
            if top_k:
                reranked = reranked[:top_k]

            logger.info("Re-ranked %d documents using LLM", len(reranked))
            return reranked

        except Exception as e:
            logger.warning("LLM re-ranking failed: %s, returning original order", str(e))
            return documents[:top_k] if top_k else documents

    def _parse_ranked_indices(self, response: str, max_index: int) -> List[int]:
        """Parse ranked indices from LLM response"""
        try:
            # Extract numbers from response
            import re
            numbers = re.findall(r'\d+', response)
            indices = [int(n) for n in numbers if int(n) < max_index]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_indices = []
            for idx in indices:
                if idx not in seen:
                    seen.add(idx)
                    unique_indices.append(idx)
            
            # Add any missing indices at the end
            all_indices = set(range(max_index))
            missing = sorted(all_indices - set(unique_indices))
            unique_indices.extend(missing)
            
            return unique_indices[:max_index]
        except Exception:
            # Fallback: return original order
            return list(range(max_index))

