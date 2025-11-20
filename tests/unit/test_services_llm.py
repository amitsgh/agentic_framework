"""Unit tests for LLM services"""

import pytest
from unittest.mock import Mock, patch
from app.services.llm.ollama_llm import OllamaLLM
from app.exceptions import LLMError


class TestOllamaLLM:
    """Tests for OllamaLLM"""

    @pytest.fixture
    def ollama_llm(self):
        """Create OllamaLLM instance"""
        return OllamaLLM(model_name="test-model")

    def test_load_model(self, ollama_llm):
        """Test loading model"""
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            ollama_llm.load_model()
            assert ollama_llm.model_name == "test-model"

    def test_model_response(self, ollama_llm):
        """Test model response"""
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"response": "Test response"}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            response = ollama_llm.model_response([{"role": "user", "content": "test"}])
            assert response == "Test response"

    def test_model_stream_response(self, ollama_llm):
        """Test model stream response"""
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.iter_lines.return_value = iter(["chunk1", "chunk2"])
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            chunks = list(ollama_llm.model_stream_response([{"role": "user", "content": "test"}]))
            assert len(chunks) > 0

    def test_model_response_error(self, ollama_llm):
        """Test model response with error"""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = Exception("Connection error")
            with pytest.raises(LLMError):
                ollama_llm.model_response([{"role": "user", "content": "test"}])


