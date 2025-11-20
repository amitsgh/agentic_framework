"""Integration tests for chat API endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestChatEndpoint:
    """Integration tests for chat endpoint"""

    @patch("app.api.v1.chat.get_llm")
    @patch("app.api.v1.chat.get_db_sync")
    @patch("app.api.v1.chat.get_embeddings")
    def test_chat_with_rag(self, mock_embeddings, mock_db, mock_llm, client):
        """Test chat endpoint with RAG"""
        mock_llm_instance = Mock()
        mock_llm_instance.model_stream_response.return_value = iter(["Hello", " world"])
        mock_llm.return_value = mock_llm_instance
        mock_db.return_value = [Mock()]
        response = client.get(
            "/api/v1/chat/chat?query=test&use_rag=true"
        )
        assert response.status_code == 200

    @patch("app.api.v1.chat.get_llm")
    def test_chat_without_rag(self, mock_llm, client):
        """Test chat endpoint without RAG"""
        mock_llm_instance = Mock()
        mock_llm_instance.model_stream_response.return_value = iter(["Response"])
        mock_llm.return_value = mock_llm_instance
        response = client.get("/api/v1/chat/chat?query=test&use_rag=false")
        assert response.status_code == 200

    def test_chat_empty_query(self, client):
        """Test chat with empty query"""
        response = client.get("/api/v1/chat/chat?query=")
        assert response.status_code == 400


