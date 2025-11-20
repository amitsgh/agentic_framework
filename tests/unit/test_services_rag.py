"""Unit tests for RAG services"""

import pytest
from unittest.mock import Mock
from app.services.rag.orchestrator import AdvancedRAGOrchestrator
from app.services.reranker.base import BaseReranker
from app.services.query_translator.base import BaseQueryTranslator
from app.services.router.base import BaseRouter, RouteTarget
from app.services.refiner.base import BaseRefiner
from app.models.document_model import Document, DocumentMetadata


class TestAdvancedRAGOrchestrator:
    """Tests for AdvancedRAGOrchestrator"""

    @pytest.fixture
    def orchestrator(self, mock_db, mock_embeddings):
        """Create AdvancedRAGOrchestrator instance"""
        from app.repositories.document_repository import DocumentRepository
        repo = DocumentRepository(mock_db)
        mock_query_translator = Mock(spec=BaseQueryTranslator)
        mock_router = Mock(spec=BaseRouter)
        mock_reranker = Mock(spec=BaseReranker)
        mock_refiner = Mock(spec=BaseRefiner)
        mock_graph_rag = Mock()
        return AdvancedRAGOrchestrator(
            document_repository=repo,
            embeddings=mock_embeddings,
            query_translator=mock_query_translator,
            router=mock_router,
            reranker=mock_reranker,
            refiner=mock_refiner,
            graph_rag=mock_graph_rag,
        )

    def test_retrieve_with_all_services(self, orchestrator, mock_embeddings):
        """Test retrieval with all RAG services"""
        mock_doc = Document(
            content="Test content",
            metadata=DocumentMetadata(source="test.pdf"),
        )
        orchestrator.document_repository.db.similarity_search.return_value = [mock_doc]
        orchestrator.query_translator.translate.return_value = ["query1", "query2"]
        orchestrator.router.route.return_value = RouteTarget.VECTOR_DB
        orchestrator.reranker.rerank.return_value = [mock_doc]
        docs, metadata = orchestrator.retrieve("test query")
        assert len(docs) > 0
        assert "query_translation" in metadata

    def test_retrieve_without_services(self, mock_db, mock_embeddings):
        """Test retrieval without advanced services"""
        from app.repositories.document_repository import DocumentRepository
        from app.services.rag.orchestrator import AdvancedRAGOrchestrator
        repo = DocumentRepository(mock_db)
        mock_doc = Document(
            content="Test",
            metadata=DocumentMetadata(source="test.pdf"),
        )
        repo.db.similarity_search.return_value = [mock_doc]
        orchestrator = AdvancedRAGOrchestrator(
            document_repository=repo,
            embeddings=mock_embeddings,
            query_translator=None,
            router=None,
            reranker=None,
            refiner=None,
            graph_rag=None,
        )
        docs, metadata = orchestrator.retrieve("test")
        assert len(docs) > 0


class TestReranker:
    """Tests for reranker services"""

    def test_llm_reranker(self):
        """Test LLM reranker"""
        from app.services.reranker.llm_reranker import LLMReranker
        from unittest.mock import Mock
        mock_llm = Mock()
        reranker = LLMReranker(llm=mock_llm)
        docs = [
            Document(content="doc1", metadata=DocumentMetadata(source="1.pdf")),
            Document(content="doc2", metadata=DocumentMetadata(source="2.pdf")),
        ]
        mock_llm.model_response.return_value = "doc2, doc1"
        result = reranker.rerank("query", docs)
        assert len(result) == 2


class TestQueryTranslator:
    """Tests for query translator services"""

    def test_multi_query_translator(self):
        """Test multi-query translator"""
        from app.services.query_translator.multi_query import MultiQueryTranslator
        from unittest.mock import Mock
        mock_llm = Mock()
        translator = MultiQueryTranslator(llm=mock_llm)
        mock_llm.model_response.return_value = "query1\nquery2\nquery3"
        queries = translator.translate("original query")
        assert len(queries) > 0


class TestRouter:
    """Tests for router services"""

    def test_llm_router(self):
        """Test LLM router"""
        from app.services.router.llm_router import LLMRouter
        from app.services.router.base import RouteTarget
        from unittest.mock import Mock
        mock_llm = Mock()
        router = LLMRouter(llm=mock_llm)
        mock_llm.model_response.return_value = "vector_db"
        target = router.route("test query")
        assert target in [RouteTarget.VECTOR_DB, RouteTarget.GRAPH_DB]


class TestRefiner:
    """Tests for refiner services"""

    def test_crag_refiner(self):
        """Test CRAG refiner"""
        from app.services.refiner.crag_refiner import CRAGRefiner
        from unittest.mock import Mock
        mock_llm = Mock()
        refiner = CRAGRefiner(llm=mock_llm)
        mock_llm.model_response.return_value = "refined answer"
        result = refiner.refine("query", "answer", [])
        assert result is not None

