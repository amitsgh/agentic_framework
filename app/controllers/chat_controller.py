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

        logger.debug("Chat method called with query length: %d", len(query))
        
        if not query or not query.strip():
            logger.warning("Empty query provided to chat method")
            raise ValidationError("Empty query provided")

        try:
            if self.rag_enabled:
                logger.debug("RAG enabled, retrieving context...")
                context_docs = self._retrieve_context(query)
                if context_docs:
                    messages = self._build_rag_prompt(query, context_docs)
                    logger.info(
                        "Using RAG with %d context documents", len(context_docs)
                    )
                    logger.debug("RAG prompt built with %d context documents", len(context_docs))
                else:
                    messages = [{"role": "user", "message": query}]
                    logger.info("RAG enabled but no context found, using direct query")
                    logger.debug("RAG retrieval returned no documents")
            else:
                logger.debug("RAG disabled, using direct query")
                messages = [{"role": "user", "message": query}]

            # TODO: inlcude logic for Message Format (prompt engineering)
            # message = [{"role": "user", "message": prompt}]
            logger.debug("Invoking LLM with %d messages", len(messages))
            response = self.llm.model_response(messages)
            logger.debug("LLM response received, length: %d", len(response))
            return response

        except Exception as e:
            logger.error("Chat error: %s", str(e), exc_info=True)
            logger.debug("Chat error for query: %s", query[:50] if len(query) > 50 else query)
            raise LLMError(f"Chat failed: {str(e)}") from e

    def chat_stream(self, query: str) -> Iterator[str]:
        """chat stream service"""

        logger.debug("Chat stream method called with query length: %d", len(query))
        
        if not query or not query.strip():
            logger.warning("Empty query provided to chat_stream method")
            raise ValidationError("Empty query provided")

        try:
            if self.rag_enabled:
                logger.debug("RAG enabled, retrieving context for stream...")
                context_docs = self._retrieve_context(query)
                if context_docs:
                    messages = self._build_rag_prompt(query, context_docs)
                    logger.info(
                        "Using RAG with %d context documents", len(context_docs)
                    )
                    logger.debug("RAG prompt built with %d context documents for stream", len(context_docs))
                else:
                    messages = [{"role": "user", "message": query}]
                    logger.info("RAG enabled but no context found, using direct query")
                    logger.debug("RAG retrieval returned no documents for stream")
            else:
                logger.debug("RAG disabled, using direct query for stream")
                messages = [{"role": "user", "message": query}]

            logger.debug("Invoking LLM stream with %d messages", len(messages))
            yield from self.llm.model_stream_response(messages)
            logger.debug("Chat stream completed successfully")

        except Exception as e:
            logger.error("Chat stream error: %s", str(e), exc_info=True)
            logger.debug("Chat stream error for query: %s", query[:50] if len(query) > 50 else query)
            raise LLMError(f"Chat stream failed: {str(e)}") from e
