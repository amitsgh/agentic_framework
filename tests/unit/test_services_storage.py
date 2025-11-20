"""Unit tests for storage services"""

import pytest
from unittest.mock import Mock, patch
from app.services.storage.minio_storage import MinIOStorage
from app.exceptions import DocumentProcessingError


class TestMinIOStorage:
    """Tests for MinIOStorage"""

    @pytest.fixture
    def minio_storage(self):
        """Create MinIOStorage instance"""
        return MinIOStorage(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket_name="test-bucket",
            secure=False,
        )

    def test_upload_file(self, minio_storage):
        """Test uploading a file"""
        with patch.object(minio_storage, "client") as mock_client:
            mock_client.put_object.return_value = None
            result = minio_storage.upload_file("test.pdf", b"content")
            assert result is not None
            mock_client.put_object.assert_called_once()

    def test_download_json(self, minio_storage):
        """Test downloading JSON"""
        with patch.object(minio_storage, "client") as mock_client:
            mock_response = Mock()
            mock_response.read.return_value = b'{"key": "value"}'
            mock_response.data = mock_response
            mock_client.get_object.return_value = mock_response
            result = minio_storage.download_json("path/to/file.json")
            assert result == {"key": "value"}

    def test_delete_object(self, minio_storage):
        """Test deleting an object"""
        with patch.object(minio_storage, "client") as mock_client:
            minio_storage.delete_object("path/to/file")
            mock_client.remove_object.assert_called_once()

    def test_object_exists(self, minio_storage):
        """Test checking if object exists"""
        with patch.object(minio_storage, "client") as mock_client:
            mock_client.stat_object.return_value = Mock()
            result = minio_storage.object_exists("path/to/file")
            assert result is True

    def test_get_object_path(self, minio_storage):
        """Test getting object path"""
        path = minio_storage.get_object_path("raw", "abc123", ".pdf")
        assert "raw" in path
        assert "abc123" in path

