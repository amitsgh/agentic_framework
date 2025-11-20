"""RAPTOR (Recursive Abstractive Processing) Service"""

from typing import List, Dict, Any

from app.models.document_model import Document
from app.services.raptor.base import BaseRaptor
from app.services.llm.base import BaseLLM
from app.services.embedder.base import BaseEmbeddings
from app.utils.logger import setuplog

logger = setuplog(__name__)


class LLMRaptor(BaseRaptor):
    """RAPTOR: Hierarchical indexing with recursive summarization"""

    def __init__(
        self,
        llm: BaseLLM,
        embeddings: BaseEmbeddings,
        cluster_size: int = 5,
        max_levels: int = 3,
    ):
        self.llm = llm
        self.embeddings = embeddings
        self.cluster_size = cluster_size
        self.max_levels = max_levels

    def build_hierarchy(self, documents: List[Document]) -> Dict[str, Any]:
        """Build hierarchical tree structure"""
        if not documents:
            return {"clusters": [], "summaries": [], "tree": {}}

        try:
            # Level 0: Original documents
            levels = [documents]
            summaries = []

            # Build hierarchy recursively
            current_level = documents
            for level in range(self.max_levels):
                if len(current_level) <= 1:
                    break

                # Cluster documents
                clusters = self._cluster_documents(current_level)

                # Summarize each cluster
                level_summaries = []
                for cluster in clusters:
                    summary = self._summarize_cluster(cluster)
                    if summary:
                        level_summaries.append(summary)
                        summaries.append({
                            "level": level + 1,
                            "summary": summary,
                            "cluster_size": len(cluster)
                        })

                if not level_summaries:
                    break

                # Create summary documents for next level
                summary_docs = [
                    Document(content=s["summary"], metadata=None)
                    for s in level_summaries
                ]
                levels.append(summary_docs)
                current_level = summary_docs

            logger.info("Built RAPTOR hierarchy with %d levels", len(levels))
            return {
                "clusters": [len(level) for level in levels],
                "summaries": summaries,
                "tree": {"levels": len(levels), "total_docs": sum(len(l) for l in levels)}
            }

        except Exception as e:
            logger.error("RAPTOR hierarchy building failed: %s", str(e))
            return {"clusters": [], "summaries": [], "tree": {}}

    def query_hierarchy(
        self, query: str, hierarchy: Dict[str, Any]
    ) -> List[Document]:
        """Query hierarchical structure"""
        # This would search through the hierarchy levels
        # For now, return empty as full implementation requires stored hierarchy
        logger.warning("RAPTOR query requires stored hierarchy structure")
        return []

    def _cluster_documents(self, documents: List[Document]) -> List[List[Document]]:
        """Cluster documents by similarity"""
        if len(documents) <= self.cluster_size:
            return [documents]

        try:
            # Simple clustering: group by sequential chunks
            clusters = []
            for i in range(0, len(documents), self.cluster_size):
                clusters.append(documents[i:i + self.cluster_size])
            return clusters
        except Exception:
            return [documents]

    def _summarize_cluster(self, cluster: List[Document]) -> str:
        """Summarize a cluster of documents"""
        try:
            cluster_text = "\n\n".join([doc.content[:500] for doc in cluster])
            prompt = f"""Summarize the following cluster of documents into a concise summary that captures the main ideas:

{cluster_text}

Summary:"""

            messages = [{"role": "user", "message": prompt}]
            summary = self.llm.model_response(messages).strip()
            return summary
        except Exception as e:
            logger.warning("Cluster summarization failed: %s", str(e))
            return ""

