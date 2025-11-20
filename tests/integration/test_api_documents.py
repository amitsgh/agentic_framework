"""Integration tests for document API endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestDocumentUpload:
    """Integration tests for document upload"""

    @patch("app.api.v1.documents.upload_document")
    def test_upload_document_success(self, mock_upload, client):
        """Test successful document upload"""
        mock_upload.return_value = {
            "status": "success",
            "file_name": "test.pdf",
            "message": "Document processed successfully",
        }
        with open("tests/fixtures/test.pdf", "rb") as f:
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_upload_invalid_file_type(self, client):
        """Test uploading invalid file type"""
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.exe", b"content", "application/x-msdownload")},
        )
        assert response.status_code == 400

    def test_upload_file_too_large(self, client):
        """Test uploading file that's too large"""
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("large.pdf", large_content, "application/pdf")},
        )
        assert response.status_code == 413


class TestDocumentDelete:
    """Integration tests for document deletion"""

    @patch("app.api.v1.documents.delete_all_documents")
    def test_delete_all_documents(self, mock_delete, client):
        """Test deleting all documents"""
        mock_delete.return_value = {
            "status": "success",
            "message": "All documents deleted",
        }
        response = client.delete("/api/v1/documents/delete-all")
        assert response.status_code == 200
        assert response.json()["status"] == "success"


