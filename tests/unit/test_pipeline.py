"""Unit tests for pipeline"""

import pytest
from unittest.mock import Mock, patch
from app.pipeline.pipeline import DocumentPipeline
from app.models.processing_state import ProcessingState, ProcessingStage
from app.models.document_model import Document, DocumentMetadata
from app.exceptions import DocumentProcessingError


class TestDocumentPipeline:
    """Tests for DocumentPipeline"""

    @pytest.fixture
    def pipeline(self, mock_extractor, mock_chunker, mock_state_manager, mock_storage):
        """Create DocumentPipeline instance"""
        return DocumentPipeline(
            extractor=mock_extractor,
            chunker=mock_chunker,
            state_manager=mock_state_manager,
            storage=mock_storage,
        )

    def test_process_new_file(self, pipeline, mock_extractor, mock_chunker, mock_storage):
        """Test processing a new file"""
        mock_extractor.extract_data.return_value = [
            Document(content="Test", metadata=DocumentMetadata(source="test.pdf"))
        ]
        mock_chunker.chunk.return_value = [
            Document(content="Chunk", metadata=DocumentMetadata(source="test.pdf"))
        ]
        mock_storage.download_json.return_value = None
        mock_storage.upload_file.return_value = "raw/test.pdf"
        result = pipeline.process("abc123", force_reprocess=False)
        assert result is not None

    def test_process_already_processed(self, pipeline, mock_storage):
        """Test processing already processed file"""
        mock_storage.download_json.return_value = [
            {"content": "chunk", "metadata": {"source": "test.pdf"}}
        ]
        result = pipeline.process("abc123", force_reprocess=False)
        assert result is not None

    def test_process_force_reprocess(self, pipeline, mock_extractor, mock_chunker):
        """Test force reprocessing"""
        mock_extractor.extract_data.return_value = []
        mock_chunker.chunk.return_value = []
        result = pipeline.process("abc123", force_reprocess=True)
        assert result is not None

    def test_process_extraction_error(self, pipeline, mock_extractor):
        """Test processing with extraction error"""
        mock_extractor.extract_data.side_effect = Exception("Extraction failed")
        with pytest.raises(DocumentProcessingError):
            pipeline.process("abc123", force_reprocess=True)

