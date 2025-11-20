"""Unit tests for managers"""

import pytest
from unittest.mock import Mock
from app.manager.state_manager import StateManager
from app.models.processing_state import ProcessingState, ProcessingStage
from app.exceptions import ValidationError


class TestStateManager:
    """Tests for StateManager"""

    @pytest.fixture
    def state_manager(self, mock_cache):
        """Create StateManager instance"""
        return StateManager(cache=mock_cache)

    def test_create_state(self, state_manager):
        """Test creating a new state"""
        state = state_manager.create_state("abc123", "test.pdf", "raw/abc123.pdf")
        assert state.file_hash == "abc123"
        assert state.filename == "test.pdf"
        assert state.stage == ProcessingStage.UPLOADED

    def test_get_state(self, state_manager, mock_cache, sample_processing_state):
        """Test getting existing state"""
        mock_cache.get.return_value = sample_processing_state.model_dump_json()
        state = state_manager.get_state("abc123")
        assert state is not None
        assert state.file_hash == "abc123"

    def test_get_state_not_found(self, state_manager, mock_cache):
        """Test getting nonexistent state"""
        mock_cache.get.return_value = None
        state = state_manager.get_state("nonexistent")
        assert state is None

    def test_update_stage(self, state_manager, sample_processing_state):
        """Test updating processing stage"""
        updated = state_manager.update_stage(
            sample_processing_state, ProcessingStage.EXTRACTED
        )
        assert updated.stage == ProcessingStage.EXTRACTED

    def test_update_stage_invalid_transition(self, state_manager, sample_processing_state):
        """Test invalid stage transition"""
        sample_processing_state.stage = ProcessingStage.STORED
        with pytest.raises(ValidationError):
            state_manager.update_stage(
                sample_processing_state, ProcessingStage.UPLOADED
            )

    def test_update_stage_with_artifact(self, state_manager, sample_processing_state):
        """Test updating stage with artifact path"""
        updated = state_manager.update_stage(
            sample_processing_state,
            ProcessingStage.EXTRACTED,
            artifact_path=("extracted", "extracted/abc123.json"),
        )
        assert updated.get_artifact_path("extracted") == "extracted/abc123.json"

    def test_clear_file_cache(self, state_manager, mock_cache):
        """Test clearing file cache"""
        result = state_manager.clear_file_cache("abc123")
        assert result is True
        mock_cache.delete.assert_called()

