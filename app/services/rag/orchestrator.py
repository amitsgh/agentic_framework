"""Advanced RAG Orchestrator - coordinates all RAG services"""

from typing import List, Optional

from app.models.document_model import Document
from app.services.reranker.base import BaseReranker
from app.services.query_translator.base import BaseQueryTranslator
from app.services.router.base import BaseRouter, RouteTarget
from app.services.refiner.base import BaseRefiner
from app.services.graph_rag.base import BaseGraphRAG
from app.repositories.document_repository import DocumentRepository
from app.services.embedder.base import BaseEmbeddings
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)


class AdvancedRAGOrchestrator:
    """Orchestrates advanced RAG pipeline with all services"""

    def __init__(
        self,
        document_repository: DocumentRepository,
        embeddings: BaseEmbeddings,
        query_translator: Optional[BaseQueryTranslator] = None,
        router: Optional[BaseRouter] = None,
        reranker: Optional[BaseReranker] = None,
        refiner: Optional[BaseRefiner] = None,
        graph_rag: Optional[BaseGraphRAG] = None,
    ):
        self.document_repository = document_repository
        self.embeddings = embeddings
        self.query_translator = query_translator
        self.router = router
        self.reranker = reranker
        self.refiner = refiner
        self.graph_rag = graph_rag

    def retrieve(
        self, query: str, top_k: int | None = None
    ) -> tuple[List[Document], dict]:
        """
        Advanced RAG retrieval pipeline:
        1. Query Translation
        2. Routing
        3. Retrieval
        4. Re-ranking
        5. Refinement
        """
        top_k = top_k or config.RAG_TOP_K
        metadata = {}

        try:
            # Step 1: Query Translation
            if config.ENABLE_QUERY_TRANSLATION and self.query_translator:
                translated_queries = self._translate_query(query)
                metadata["translated_queries"] = translated_queries
                logger.info("Query translated to %d variations", len(translated_queries))
            else:
                translated_queries = [query]

            # Step 2: Routing
            route_info = None
            if config.ENABLE_ROUTING and self.router:
                route_info = self.router.route(query)
                metadata["routing"] = route_info
                logger.info("Query routed to: %s", route_info["target"].value)

            # Step 3: Retrieval
            documents = self._retrieve_documents(translated_queries, route_info, top_k)

            # Step 4: Re-ranking
            if config.ENABLE_RERANKING and self.reranker and documents:
                documents = self.reranker.rerank(query, documents, top_k)
                metadata["reranked"] = True
                logger.info("Re-ranked %d documents", len(documents))

            # Step 5: Refinement (CRAG)
            if config.ENABLE_REFINEMENT and self.refiner and documents:
                documents, needs_retrieval = self.refiner.refine(query, documents)
                metadata["refined"] = True
                metadata["needs_retrieval"] = needs_retrieval
                
                if needs_retrieval:
                    logger.info("Refinement indicated need for re-retrieval")
                    # Optionally trigger re-retrieval here

            metadata["final_count"] = len(documents)
            return documents, metadata

        except Exception as e:
            logger.error("Advanced RAG retrieval failed: %s", str(e), exc_info=True)
            # Fallback to simple retrieval
            return self._simple_retrieve(query, top_k), metadata

    def _translate_query(self, query: str) -> List[str]:
        """Translate query using translator"""
        result = self.query_translator.translate(query)
        if isinstance(result, str):
            return [result]
        return result

    def _retrieve_documents(
        self,
        queries: List[str],
        route_info: Optional[dict],
        top_k: int,
    ) -> List[Document]:
        """Retrieve documents based on queries and routing"""
        all_documents = []
        seen_ids = set()

        # Determine retrieval strategy
        if route_info and route_info["target"] == RouteTarget.GRAPH_DB:
            if self.graph_rag and config.ENABLE_GRAPH_RAG:
                # Graph RAG retrieval
                for query in queries:
                    graph_docs = self.graph_rag.query(query)
                    all_documents.extend(graph_docs)
        elif route_info and route_info["target"] == RouteTarget.MULTI:
            # Multi-source retrieval
            for query in queries:
                # Vector DB
                vec_docs = self.document_repository.similarity_search(
                    query, self.embeddings, top_k=top_k
                )
                all_documents.extend(vec_docs)
                
                # Graph DB if available
                if self.graph_rag and config.ENABLE_GRAPH_RAG:
                    graph_docs = self.graph_rag.query(query)
                    all_documents.extend(graph_docs)
        else:
            # Default: Vector DB retrieval
            for query in queries:
                docs = self.document_repository.similarity_search(
                    query, self.embeddings, top_k=top_k
                )
                all_documents.extend(docs)

        # Deduplicate by content
        unique_docs = []
        for doc in all_documents:
            doc_id = hash(doc.content)
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_docs.append(doc)

        logger.info("Retrieved %d unique documents from %d queries", len(unique_docs), len(queries))
        return unique_docs

    def _simple_retrieve(self, query: str, top_k: int) -> List[Document]:
        """Simple fallback retrieval"""
        return self.document_repository.similarity_search(
            query, self.embeddings, top_k=top_k
        )

