"""Unit tests for repositories"""

import pytest
from app.repositories.document_repository import DocumentRepository
from app.repositories.cache_repository import CacheRepository
from app.exceptions import DatabaseError, ValidationError


class TestDocumentRepository:
    """Tests for DocumentRepository"""

    def test_add_documents_success(self, mock_db, mock_embeddings, sample_documents):
        """Test successfully adding documents"""
        repo = DocumentRepository(mock_db)
        ids = repo.add_documents(sample_documents, mock_embeddings)
        assert len(ids) == 2
        mock_db.add_documents.assert_called_once()

    def test_add_documents_empty_list(self, mock_db, mock_embeddings):
        """Test adding empty document list"""
        repo = DocumentRepository(mock_db)
        with pytest.raises(DatabaseError, match="No documents provided"):
            repo.add_documents([], mock_embeddings)

    def test_add_documents_db_error(self, mock_db, mock_embeddings, sample_documents):
        """Test database error during add"""
        mock_db.add_documents.side_effect = Exception("DB connection failed")
        repo = DocumentRepository(mock_db)
        with pytest.raises(DatabaseError):
            repo.add_documents(sample_documents, mock_embeddings)

    def test_similarity_search_success(self, mock_db, mock_embeddings):
        """Test successful similarity search"""
        mock_docs = [pytest.fixture(sample_document)()]
        mock_db.similarity_search.return_value = mock_docs
        repo = DocumentRepository(mock_db)
        results = repo.similarity_search("test query", mock_embeddings, top_k=5)
        assert len(results) > 0
        mock_db.similarity_search.assert_called_once()

    def test_similarity_search_empty_query(self, mock_db, mock_embeddings):
        """Test similarity search with empty query"""
        repo = DocumentRepository(mock_db)
        results = repo.similarity_search("", mock_embeddings)
        assert results == []
        mock_db.similarity_search.assert_not_called()

    def test_delete_all_documents(self, mock_db):
        """Test deleting all documents"""
        repo = DocumentRepository(mock_db)
        result = repo.delete_all_documents()
        assert result is True
        mock_db.delete_all.assert_called_once()

    def test_delete_all_db_error(self, mock_db):
        """Test database error during delete all"""
        mock_db.delete_all.side_effect = Exception("DB error")
        repo = DocumentRepository(mock_db)
        with pytest.raises(DatabaseError):
            repo.delete_all_documents()


class TestCacheRepository:
    """Tests for CacheRepository"""

    def test_save_state(self, mock_cache, sample_processing_state):
        """Test saving processing state"""
        repo = CacheRepository(mock_cache)
        result = repo.save(sample_processing_state)
        assert result is True
        mock_cache.set.assert_called_once()

    def test_get_state(self, mock_cache, sample_processing_state):
        """Test getting processing state"""
        mock_cache.get.return_value = sample_processing_state.model_dump_json()
        repo = CacheRepository(mock_cache)
        state = repo.get("abc123")
        assert state is not None
        mock_cache.get.assert_called_once()

    def test_get_state_not_found(self, mock_cache):
        """Test getting nonexistent state"""
        mock_cache.get.return_value = None
        repo = CacheRepository(mock_cache)
        state = repo.get("nonexistent")
        assert state is None

    def test_delete_state(self, mock_cache):
        """Test deleting state"""
        repo = CacheRepository(mock_cache)
        result = repo.delete("abc123")
        assert result is True
        mock_cache.delete.assert_called_once()

