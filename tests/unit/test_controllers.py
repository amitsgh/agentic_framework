"""Unit tests for controllers"""

import pytest
from unittest.mock import Mock
from app.controllers.chat_controller import ChatController
from app.controllers.document_controller import DocumentController
from app.exceptions import ValidationError, LLMError, DocumentProcessingError


class TestChatController:
    """Tests for ChatController"""

    def test_init_with_rag(self, mock_llm, mock_db, mock_embeddings):
        """Test ChatController initialization with RAG"""
        from app.repositories.document_repository import DocumentRepository
        repo = DocumentRepository(mock_db)
        controller = ChatController(
            llm=mock_llm,
            document_repository=repo,
            embeddings=mock_embeddings,
            use_rag=True,
        )
        assert controller.use_rag is True

    def test_init_without_rag(self, mock_llm):
        """Test ChatController initialization without RAG"""
        controller = ChatController(llm=mock_llm, use_rag=False)
        assert controller.use_rag is False

    def test_chat_stream_success(self, mock_llm):
        """Test successful chat streaming"""
        controller = ChatController(llm=mock_llm, use_rag=False)
        response = list(controller.chat_stream("Hello"))
        assert len(response) > 0
        mock_llm.model_stream_response.assert_called_once()

    def test_chat_stream_empty_query(self, mock_llm):
        """Test chat stream with empty query"""
        controller = ChatController(llm=mock_llm, use_rag=False)
        with pytest.raises(ValidationError, match="Empty query"):
            list(controller.chat_stream(""))

    def test_chat_stream_llm_error(self, mock_llm):
        """Test chat stream with LLM error"""
        mock_llm.model_stream_response.side_effect = Exception("LLM error")
        controller = ChatController(llm=mock_llm, use_rag=False)
        with pytest.raises(LLMError):
            list(controller.chat_stream("test"))

    def test_build_messages_with_rag(self, mock_llm, mock_db, mock_embeddings):
        """Test building messages with RAG context"""
        from app.repositories.document_repository import DocumentRepository
        from app.models.document_model import Document, DocumentMetadata
        repo = DocumentRepository(mock_db)
        mock_doc = Document(
            content="Test content",
            metadata=DocumentMetadata(source="test.pdf"),
        )
        mock_db.similarity_search.return_value = [mock_doc]
        controller = ChatController(
            llm=mock_llm,
            document_repository=repo,
            embeddings=mock_embeddings,
            use_rag=True,
        )
        messages = controller._build_messages("test query")
        assert len(messages) > 0
        assert any("Test content" in str(msg) for msg in messages)


class TestDocumentController:
    """Tests for DocumentController"""

    @pytest.fixture
    def mock_pipeline(self):
        """Mock pipeline"""
        return Mock()

    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager"""
        return Mock()

    def test_upload_success(
        self, mock_pipeline, mock_state_manager, mock_db, mock_storage, mock_embeddings
    ):
        """Test successful document upload"""
        from app.repositories.document_repository import DocumentRepository
        from app.controllers.document_controller import DocumentController
        from unittest.mock import Mock
        repo = DocumentRepository(mock_db)
        controller = DocumentController(
            pipeline=mock_pipeline,
            state_manager=mock_state_manager,
            document_repository=repo,
            storage=mock_storage,
        )
        mock_pipeline.process.return_value = ([], Mock())
        result = controller.upload("test.pdf", "abc123", "test.pdf", mock_embeddings)
        assert result is not None

    def test_upload_already_processed(
        self, mock_state_manager, mock_db, mock_storage, mock_embeddings
    ):
        """Test upload of already processed document"""
        from app.repositories.document_repository import DocumentRepository
        from app.controllers.document_controller import DocumentController
        from app.models.processing_state import ProcessingState, ProcessingStage
        from unittest.mock import Mock
        repo = DocumentRepository(mock_db)
        state = ProcessingState(
            file_hash="abc123",
            filename="test.pdf",
            stage=ProcessingStage.STORED,
        )
        mock_state_manager.get_state.return_value = state
        controller = DocumentController(
            pipeline=Mock(),
            state_manager=mock_state_manager,
            document_repository=repo,
            storage=mock_storage,
        )
        mock_storage.download_json.return_value = [
            {"content": "test", "metadata": {"source": "test.pdf"}}
        ]
        result = controller.upload("test.pdf", "abc123", "test.pdf", mock_embeddings)
        assert result is not None

