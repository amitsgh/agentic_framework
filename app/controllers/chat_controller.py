"""Controller for chat"""

from typing import Iterator, List, Dict

from app.services.llm.base import BaseLLM
from app.services.db.base import BaseDB
from app.services.embedder.base import BaseEmbeddings
from app.models.document_model import Document
from app.core.exceptions.base import LLMError, DatabaseError, ValidationError
from app.core.config import config
from app.core.logger import setuplog

logger = setuplog(__name__)


class ChatController:
    """Controller for chat with RAG support"""

    def __init__(
        self,
        llm: BaseLLM,
        db: BaseDB | None = None,
        embeddings: BaseEmbeddings | None = None,
    ):
        self.llm = llm
        self.db = db
        self.embeddings = embeddings
        self.rag_enabled = (
            config.RAG_ENABLED and db is not None and embeddings is not None
        )

    def _build_rag_prompt(self, query: str, context_docs: List[Document]) -> List[Dict[str, str]]:
        """Build prompt with RAG context"""

        context = "\n\n".join([doc.content for doc in context_docs])
        prompt = f"""Answer the following question based on the provided context.
            Context:
            {context}

            Question: {query}

            Answer:
            """

        message = [{"role": "user", "message": prompt}]
        return message

    def _retrieve_context(self, query: str) -> List[Document]:
        """Retrieve relevant documents for RAG"""

        if not self.rag_enabled:
            return []

        try:
            if self.db is None or self.embeddings is None:
                logger.warning("RAG retrieval failed: DB or embeddings is None")
                return []

            return self.db.similarity_search(
                query=query, embeddings=self.embeddings, top_k=config.RAG_TOP_K
            )

        except (DatabaseError, ValidationError) as e:
            logger.warning("RAG retrieval failed: %s", str(e))
            return []
        except Exception as e:
            logger.warning("Unexpected error during RAG retrieval: %s", str(e))
            return []

    def chat(self, query: str) -> str:
        """chat service"""

        if not query or not query.strip():
            raise ValidationError("Empty query provided")

        try:
            if self.rag_enabled:
                context_docs = self._retrieve_context(query)
                if context_docs:
                    messages = self._build_rag_prompt(query, context_docs)
                    logger.info(
                        "Using RAG with %d context documents", len(context_docs)
                    )
                else:
                    messages = [{"role": "user", "message": query}]
                    logger.info("RAG enabled but no context found, using direct query")
            else:
                messages = [{"role": "user", "message": query}]

            # TODO: inlcude logic for Message Format (prompt engineering)
            # message = [{"role": "user", "message": prompt}]
            response = self.llm.model_response(messages)
            return response

        except Exception as e:
            logger.error("Chat error: %s", str(e), exc_info=True)
            raise LLMError(f"Chat failed: {str(e)}") from e

    def chat_stream(self, query: str) -> Iterator[str]:
        """chat stream service"""

        if not query or not query.strip():
            raise ValidationError("Empty query provided")

        try:
            if self.rag_enabled:
                context_docs = self._retrieve_context(query)
                if context_docs:
                    messages = self._build_rag_prompt(query, context_docs)
                    logger.info(
                        "Using RAG with %d context documents", len(context_docs)
                    )
                else:
                    messages = [{"role": "user", "message": query}]
                    logger.info("RAG enabled but no context found, using direct query")
            else:
                messages = [{"role": "user", "message": query}]

            yield from self.llm.model_stream_response(messages)

        except Exception as e:
            logger.error("Chat stream error: %s", str(e), exc_info=True)
            raise LLMError(f"Chat stream failed: {str(e)}") from e
