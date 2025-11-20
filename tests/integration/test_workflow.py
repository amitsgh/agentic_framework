"""Integration tests for complete workflows"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.models.document_model import Document, DocumentMetadata
from app.models.processing_state import ProcessingState, ProcessingStage


class TestDocumentProcessingWorkflow:
    """Integration tests for document processing workflow"""

    @pytest.fixture
    def mock_services(self):
        """Create mock services for workflow testing"""
        return {
            "extractor": Mock(),
            "chunker": Mock(),
            "embeddings": Mock(),
            "db": Mock(),
            "cache": Mock(),
            "storage": Mock(),
        }

    def test_complete_document_processing_workflow(self, mock_services):
        """Test complete document processing workflow"""
        # Setup mocks
        doc = Document(
            content="Test content",
            metadata=DocumentMetadata(source="test.pdf"),
        )
        mock_services["extractor"].extract_data.return_value = [doc]
        mock_services["chunker"].chunk.return_value = [doc]
        mock_services["embeddings"].embed_documents.return_value = [[0.1] * 384]
        mock_services["db"].add_documents.return_value = ["doc1"]
        mock_services["storage"].upload_file.return_value = "raw/test.pdf"
        mock_services["storage"].download_json.return_value = None

        # Simulate workflow
        from app.pipeline.pipeline import DocumentPipeline
        from app.manager.state_manager import StateManager
        from app.repositories.cache_repository import CacheRepository

        state_manager = StateManager(cache=mock_services["cache"])
        cache_repo = CacheRepository(mock_services["cache"])

        pipeline = DocumentPipeline(
            extractor=mock_services["extractor"],
            chunker=mock_services["chunker"],
            state_manager=state_manager,
            storage=mock_services["storage"],
        )

        # Process document
        state = state_manager.create_state("abc123", "test.pdf", "raw/test.pdf")
        cache_repo.save(state)

        docs, final_state = pipeline.process("abc123", force_reprocess=False)

        assert final_state is not None
        assert final_state.stage in [ProcessingStage.CHUNKED, ProcessingStage.STORED]


class TestRAGWorkflow:
    """Integration tests for RAG workflow"""

    @pytest.fixture
    def mock_rag_services(self):
        """Create mock RAG services"""
        return {
            "llm": Mock(),
            "embeddings": Mock(),
            "db": Mock(),
            "query_translator": Mock(),
            "router": Mock(),
            "reranker": Mock(),
            "refiner": Mock(),
        }

    def test_rag_chat_workflow(self, mock_rag_services):
        """Test complete RAG chat workflow"""
        # Setup
        mock_doc = Document(
            content="Relevant content",
            metadata=DocumentMetadata(source="test.pdf"),
        )
        mock_rag_services["db"].similarity_search.return_value = [mock_doc]
        mock_rag_services["embeddings"].embed_query.return_value = [0.1] * 384
        mock_rag_services["llm"].model_stream_response.return_value = iter(["Answer"])

        from app.controllers.chat_controller import ChatController
        from app.repositories.document_repository import DocumentRepository

        repo = DocumentRepository(mock_rag_services["db"])
        controller = ChatController(
            llm=mock_rag_services["llm"],
            document_repository=repo,
            embeddings=mock_rag_services["embeddings"],
            use_rag=True,
        )

        # Execute
        response = list(controller.chat_stream("test query"))

        assert len(response) > 0
        mock_rag_services["db"].similarity_search.assert_called_once()

