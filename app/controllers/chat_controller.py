"""Chat controller - orchestration only"""

from typing import Iterator, Optional
from app.services.llm.base import BaseLLM
from app.repositories.document_repository import DocumentRepository
from app.services.embedder.base import BaseEmbeddings
from app.config import config
from app.exceptions import LLMError, ValidationError
from app.utils.logger import setuplog

logger = setuplog(__name__)


class ChatController:
    """Orchestrates chat-related operations"""

    def __init__(
        self,
        llm: BaseLLM,
        document_repository: Optional[DocumentRepository] = None,
        embeddings: Optional[BaseEmbeddings] = None,
        use_rag: bool = True,
    ):
        self.llm = llm
        self.document_repository = document_repository
        self.embeddings = embeddings
        self.use_rag = use_rag and document_repository is not None and embeddings is not None

    def chat_stream(self, query: str) -> Iterator[str]:
        """Orchestrate chat streaming with optional RAG"""
        if not query or not query.strip():
            raise ValidationError("Empty query provided")

        try:
            messages = self._build_messages(query)
            yield from self.llm.model_stream_response(messages)
        except ValidationError:
            raise
        except Exception as e:
            logger.error("Chat error: %s", str(e), exc_info=True)
            raise LLMError(f"Chat failed: {str(e)}") from e

    def _build_messages(self, query: str) -> list[dict[str, str]]:
        """Build messages with optional RAG context"""
        if not self.use_rag:
            return [{"role": "user", "message": query}]

        try:
            if self.document_repository is None or self.embeddings is None:
                return [{"role": "user", "message": query}]

            context_docs = self.document_repository.similarity_search(
                query=query, embeddings=self.embeddings, top_k=config.RAG_TOP_K
            )

            if context_docs:
                context = "\n\n".join([doc.content for doc in context_docs])
                prompt = f"""Answer the following question based on the provided context.
Context:
{context}

Question: {query}

Answer:
"""
                return [{"role": "user", "message": prompt}]
        except Exception as e:
            logger.warning("RAG retrieval failed: %s", str(e))

        return [{"role": "user", "message": query}]
