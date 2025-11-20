"""Unit tests for embeddings services"""

import pytest
from unittest.mock import Mock, patch
from app.services.embedder.huggingface_embedder import HuggingFaceEmbeddigns
from app.exceptions import EmbeddingError


class TestHuggingFaceEmbedder:
    """Tests for HuggingFaceEmbedder"""

    @pytest.fixture
    def embedder(self):
        """Create HuggingFaceEmbedder instance"""
        return HuggingFaceEmbeddigns(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def test_embed_single_text(self, embedder):
        """Test embedding a single text"""
        with patch.object(embedder, "model") as mock_model:
            mock_model.encode.return_value = [[0.1] * 384]
            result = embedder.embed("test query")
            assert result.shape[0] == 1
            assert result.shape[1] == 384
            mock_model.encode.assert_called_once()

    def test_embed_multiple_texts(self, embedder):
        """Test embedding multiple texts"""
        with patch.object(embedder, "model") as mock_model:
            mock_model.encode.return_value = [[0.1] * 384, [0.2] * 384]
            result = embedder.embed(["doc1", "doc2"])
            assert result.shape[0] == 2
            mock_model.encode.assert_called_once()

    def test_embed_error(self, embedder):
        """Test embedding with error"""
        with patch.object(embedder, "model") as mock_model:
            mock_model.encode.side_effect = Exception("Model error")
            with pytest.raises(Exception):
                embedder.embed("test")

