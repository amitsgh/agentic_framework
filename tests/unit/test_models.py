"""Unit tests for models"""

import pytest
from app.models.document_model import Document, DocumentMetadata
from app.models.processing_state import ProcessingState, ProcessingStage


class TestDocumentMetadata:
    """Tests for DocumentMetadata model"""

    def test_create_metadata(self):
        """Test creating DocumentMetadata with required fields"""
        metadata = DocumentMetadata(source="test.pdf", page_number=1)
        assert metadata.source == "test.pdf"
        assert metadata.page_number == 1
        assert metadata.content_layer is None

    def test_metadata_optional_fields(self):
        """Test DocumentMetadata with optional fields"""
        metadata = DocumentMetadata(
            source="test.pdf",
            page_number=1,
            content_layer="text",
            mimetype="application/pdf",
        )
        assert metadata.content_layer == "text"
        assert metadata.mimetype == "application/pdf"


class TestDocument:
    """Tests for Document model"""

    def test_create_document(self, sample_document):
        """Test creating a Document"""
        assert sample_document.content == "This is a test document content."
        assert sample_document.metadata.source == "test.pdf"

    def test_document_without_metadata(self):
        """Test creating Document without metadata"""
        doc = Document(content="Test content")
        assert doc.content == "Test content"
        assert doc.metadata is None


class TestProcessingStage:
    """Tests for ProcessingStage enum"""

    def test_stage_values(self):
        """Test ProcessingStage enum values"""
        assert ProcessingStage.UPLOADED == "uploaded"
        assert ProcessingStage.EXTRACTED == "extracted"
        assert ProcessingStage.CHUNKED == "chunked"
        assert ProcessingStage.STORED == "stored"
        assert ProcessingStage.FAILED == "failed"

    def test_valid_transitions(self):
        """Test valid stage transitions"""
        transitions = ProcessingStage.get_valid_transitions()
        assert ProcessingStage.EXTRACTED in transitions[ProcessingStage.UPLOADED]
        assert ProcessingStage.FAILED in transitions[ProcessingStage.UPLOADED]
        assert ProcessingStage.CHUNKED in transitions[ProcessingStage.EXTRACTED]

    def test_can_transition_to(self):
        """Test can_transition_to method"""
        stage = ProcessingStage.UPLOADED
        assert stage.can_transition_to(ProcessingStage.EXTRACTED) is True
        assert stage.can_transition_to(ProcessingStage.FAILED) is True
        assert stage.can_transition_to(ProcessingStage.STORED) is False

    def test_invalid_transition(self):
        """Test invalid transitions"""
        stage = ProcessingStage.STORED
        assert stage.can_transition_to(ProcessingStage.UPLOADED) is False


class TestProcessingState:
    """Tests for ProcessingState model"""

    def test_create_processing_state(self, sample_processing_state):
        """Test creating ProcessingState"""
        assert sample_processing_state.file_hash == "abc123"
        assert sample_processing_state.filename == "test.pdf"
        assert sample_processing_state.stage == ProcessingStage.UPLOADED

    def test_processing_state_artifact_paths(self):
        """Test ProcessingState with artifact paths"""
        state = ProcessingState(
            file_hash="abc123",
            filename="test.pdf",
            stage=ProcessingStage.CHUNKED,
            artifact_paths={
                "raw": "raw/abc123.pdf",
                "extracted": "extracted/abc123.json",
                "chunks": "chunks/abc123.json",
            },
        )
        assert state.get_artifact_path("raw") == "raw/abc123.pdf"
        assert state.get_artifact_path("chunks") == "chunks/abc123.json"

    def test_set_artifact_path(self, sample_processing_state):
        """Test setting artifact path"""
        sample_processing_state.set_artifact_path("raw", "raw/test.pdf")
        assert sample_processing_state.get_artifact_path("raw") == "raw/test.pdf"

    def test_get_nonexistent_artifact_path(self, sample_processing_state):
        """Test getting nonexistent artifact path"""
        assert sample_processing_state.get_artifact_path("nonexistent") is None

