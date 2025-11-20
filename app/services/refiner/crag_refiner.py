"""CRAG (Critique and Revise Augmented Generation) Refinement Service"""

from typing import List

from app.models.document_model import Document
from app.services.refiner.base import BaseRefiner
from app.services.llm.base import BaseLLM
from app.utils.logger import setuplog

logger = setuplog(__name__)


class CRAGRefiner(BaseRefiner):
    """Refine documents using CRAG methodology"""

    def __init__(self, llm: BaseLLM, relevance_threshold: float = 0.7):
        self.llm = llm
        self.relevance_threshold = relevance_threshold

    def refine(
        self, query: str, documents: List[Document]
    ) -> tuple[List[Document], bool]:
        """
        Refine documents using CRAG:
        1. Critique documents for relevance
        2. Revise/keep only relevant ones
        3. Determine if new retrieval is needed
        """
        if not documents:
            return [], True  # Need retrieval if no documents

        try:
            # Step 1: Critique documents
            relevant_docs = []
            needs_retrieval = False

            for doc in documents:
                is_relevant = self._critique_document(query, doc)
                if is_relevant:
                    relevant_docs.append(doc)
                else:
                    needs_retrieval = True  # If any doc is irrelevant, may need retrieval

            # Step 2: If too few relevant docs, flag for retrieval
            if len(relevant_docs) < len(documents) * self.relevance_threshold:
                needs_retrieval = True

            # Step 3: Revise documents (summarize/compress if needed)
            refined_docs = self._revise_documents(query, relevant_docs)

            logger.info(
                "CRAG refined %d/%d documents, needs_retrieval=%s",
                len(refined_docs),
                len(documents),
                needs_retrieval
            )

            return refined_docs, needs_retrieval

        except Exception as e:
            logger.warning("CRAG refinement failed: %s", str(e))
            return documents, False

    def _critique_document(self, query: str, document: Document) -> bool:
        """Critique if document is relevant to query"""
        try:
            prompt = f"""Is the following document relevant to answering this query?

Query: {query}

Document: {document.content[:500]}

Respond with only "yes" or "no":"""

            messages = [{"role": "user", "message": prompt}]
            response = self.llm.model_response(messages).strip().lower()

            return "yes" in response

        except Exception:
            # Default to relevant if critique fails
            return True

    def _revise_documents(
        self, query: str, documents: List[Document]
    ) -> List[Document]:
        """Revise documents (summarize/compress)"""
        # For now, return as-is. Can be enhanced with summarization
        return documents

