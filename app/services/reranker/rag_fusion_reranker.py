"""RAG-Fusion Re-ranking Service"""

from typing import List

from app.models.document_model import Document
from app.services.reranker.base import BaseReranker
from app.services.embedder.base import BaseEmbeddings
from app.utils.logger import setuplog

logger = setuplog(__name__)


class RAGFusionReranker(BaseReranker):
    """Re-ranker using RAG-Fusion (reciprocal rank fusion)"""

    def __init__(self, embeddings: BaseEmbeddings):
        self.embeddings = embeddings

    def rerank(
        self, query: str, documents: List[Document], top_k: int | None = None
    ) -> List[Document]:
        """Re-rank using reciprocal rank fusion"""
        if not documents:
            return []

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed(query)
            
            # Score each document
            scored_docs = []
            for doc in documents:
                doc_embedding = self.embeddings.embed(doc.content)
                # Cosine similarity
                import numpy as np
                similarity = np.dot(query_embedding, doc_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                )
                scored_docs.append((similarity, doc))

            # Sort by score (descending)
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            reranked = [doc for _, doc in scored_docs]

            if top_k:
                reranked = reranked[:top_k]

            logger.info("Re-ranked %d documents using RAG-Fusion", len(reranked))
            return reranked

        except Exception as e:
            logger.warning("RAG-Fusion re-ranking failed: %s", str(e))
            return documents[:top_k] if top_k else documents

