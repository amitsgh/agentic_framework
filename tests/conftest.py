"""Pytest configuration and shared fixtures"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Generator

from app.models.document_model import Document, DocumentMetadata
from app.models.processing_state import ProcessingState, ProcessingStage
from app.services.llm.base import BaseLLM
from app.services.embedder.base import BaseEmbeddings
from app.services.db.base import BaseDB
from app.services.cache.base import BaseCache
from app.services.extractor.base import BaseExtractor
from app.services.chunker.base import BaseChunker
from app.services.storage.base import BaseStorage


@pytest.fixture
def mock_llm() -> Mock:
    """Mock LLM service"""
    llm = Mock(spec=BaseLLM)
    llm.model_response.return_value = "Test response"
    llm.model_stream_response.return_value = iter(["Test", " response"])
    return llm


@pytest.fixture
def mock_embeddings() -> Mock:
    """Mock embeddings service"""
    embeddings = Mock(spec=BaseEmbeddings)
    embeddings.embed_query.return_value = [0.1] * 384
    embeddings.embed_documents.return_value = [[0.1] * 384]
    return embeddings


@pytest.fixture
def mock_db() -> Mock:
    """Mock database service"""
    db = Mock(spec=BaseDB)
    db.add_documents.return_value = ["doc1", "doc2"]
    db.similarity_search.return_value = []
    db.delete_all.return_value = True
    return db


@pytest.fixture
def mock_cache() -> Mock:
    """Mock cache service"""
    cache = Mock(spec=BaseCache)
    cache.get.return_value = None
    cache.set.return_value = True
    cache.delete.return_value = True
    cache.exists.return_value = False
    return cache


@pytest.fixture
def mock_extractor() -> Mock:
    """Mock extractor service"""
    extractor = Mock(spec=BaseExtractor)
    extractor.extract_data.return_value = []
    return extractor


@pytest.fixture
def mock_chunker() -> Mock:
    """Mock chunker service"""
    chunker = Mock(spec=BaseChunker)
    chunker.chunk.return_value = []
    return chunker


@pytest.fixture
def mock_storage() -> Mock:
    """Mock storage service"""
    storage = Mock(spec=BaseStorage)
    storage.upload_file.return_value = "path/to/file"
    storage.download_json.return_value = {}
    storage.delete_object.return_value = True
    storage.object_exists.return_value = False
    return storage


@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing"""
    metadata = DocumentMetadata(
        source="test.pdf",
        page_number=1,
    )
    return Document(
        content="This is a test document content.",
        metadata=metadata,
    )


@pytest.fixture
def mock_pipeline():
    """Mock pipeline"""
    from unittest.mock import Mock
    return Mock()


@pytest.fixture
def mock_state_manager():
    """Mock state manager"""
    from unittest.mock import Mock
    return Mock()


@pytest.fixture
def sample_documents() -> list[Document]:
    """Create sample documents for testing"""
    return [
        Document(
            content=f"Document {i} content.",
            metadata=DocumentMetadata(source=f"test_{i}.pdf", page_number=i),
        )
        for i in range(3)
    ]


@pytest.fixture
def sample_processing_state() -> ProcessingState:
    """Create a sample processing state"""
    return ProcessingState(
        file_hash="abc123",
        filename="test.pdf",
        stage=ProcessingStage.UPLOADED,
    )


@pytest.fixture
def sample_file_content() -> bytes:
    """Sample file content for testing"""
    return b"Sample PDF content for testing"


@pytest.fixture
def sample_file_hash() -> str:
    """Sample file hash"""
    return "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

