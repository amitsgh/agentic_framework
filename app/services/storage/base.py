"""Base Storage Service"""

from typing import Any, Dict, List, Union


class BaseStorage:
    """Abstract base class for storage services."""

    def upload_file(
        self, file_path: str, object_name: str, content_type: str = ""
    ) -> str:
        """Upload a file to storage."""
        raise NotImplementedError("upload_file must be implemented in subclass")

    def upload_bytes(
        self, data: bytes, object_name: str, content_type: str = ""
    ) -> str:
        """Upload bytes to storage."""
        raise NotImplementedError("upload_bytes must be implemented in subclass")

    def download_file(self, object_name: str, file_path: str) -> None:
        """Download a file from storage."""
        raise NotImplementedError("download_file must be implemented in subclass")

    def download_bytes(self, object_name: str) -> bytes:
        """Download object as bytes."""
        raise NotImplementedError("download_bytes must be implemented in subclass")

    def upload_json(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]], object_name: str
    ) -> str:
        """Upload JSON data to storage."""
        raise NotImplementedError("upload_json must be implemented in subclass")

    def download_json(
        self, object_name: str
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Download and parse JSON from storage."""
        raise NotImplementedError("download_json must be implemented in subclass")

    def delete_object(self, object_name: str) -> None:
        """Delete object from storage."""
        raise NotImplementedError("delete_object must be implemented in subclass")

    def object_exists(self, object_name: str) -> bool:
        """Check if object exists in storage."""
        raise NotImplementedError("object_exists must be implemented in subclass")

    def get_object_path(
        self, artifact_type: str, file_hash: str, extension: str = ""
    ) -> str:
        """Generate standardized object path."""
        raise NotImplementedError("get_object_path must be implemented in subclass")
