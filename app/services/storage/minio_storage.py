"""MinIO Storage Service"""

import json
from typing import Optional, List, Dict, Any
from pathlib import Path
import io

from minio import Minio
from minio.error import S3Error

from app.config import config
from app.utils.logger import setuplog


logger = setuplog(__name__)


class MinIOStorage:
    """MinIO storage service for pesistent artifacts"""

    def __int__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        secure: bool = False,
    ):
        self.endpoint = endpoint or config.MINIO_ENDPOINT
        self.access_key = access_key or config.MINIO_ACCESS_KEY
        self.secret_key = secret_key or config.MINIO_SECRET_KEY
        self.bucket_name = bucket_name or config.MINIO_BUCKET_NAME
        self.secure = secure

        self._client = self._connect()
        self._ensure_bucket()
        logger.info(
            "Initialized MinIOStorage with endpoint=%s, bucket_name=%s, secure=%s",
            self.endpoint, self.bucket_name, self.secure,
        )

    def _connect(self) -> Minio:
        """Connect to MinIO client"""

        logger.debug("Connecting to MinIO at endpoint: %s", self.endpoint)
        client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,  # Set to True if using SSL/TLS
        )

        logger.debug("MinIO client created successfully")
        return client

    def _get_client(self) -> Minio:
        """Get or create MinIO client"""
        if self._client is None:
            logger.warning("MinIO client not initialized, reconnecting...")
            self._client = self._connect()

        return self._client

    def _ensure_bucket(self) -> None:
        """Ensure bucket exists"""
        try:
            client = self._get_client()
            if not client.bucket_exists(self.bucket_name):
                logger.info("Bucket %s does not exist. Creating...", self.bucket_name)
                client.make_bucket(self.bucket_name)
                logger.info("Created MinIO bucket: %s", self.bucket_name)
            else:
                logger.debug("MinIO bucket already exists: %s", self.bucket_name)
        except S3Error as e:
            logger.error("Failed to ensure MinIO bucket: %s", str(e), exc_info=True)
            raise

    def upload_file(
        self, file_path: str, object_name: str, content_type: str = ""
    ) -> str:
        """Upload file to MinIO"""
        try:
            client = self._get_client()
            logger.debug("Uploading file %s as object %s to bucket %s", file_path, object_name, self.bucket_name)
            client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
                content_type=content_type,
            )
            logger.info("Uploaded file to MinIO: %s", object_name)
            return object_name
        except S3Error as e:
            logger.error("Failed to upload file to MinIO: %s", str(e), exc_info=True)
            raise

    def upload_bytes(
        self, data: bytes, object_name: str, content_type: str = ""
    ) -> str:
        """Upload bytes to MinIO"""
        try:
            client = self._get_client()
            logger.debug("Uploading bytes as object %s to bucket %s", object_name, self.bucket_name)
            data_stream = io.BytesIO(data)
            client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type,
            )
            logger.info("Uploaded bytes to MinIO: %s", object_name)
            return object_name
        except S3Error as e:
            logger.error("Failed to upload bytes to MinIO: %s", str(e), exc_info=True)
            raise

    def download_file(self, object_name: str, file_path: str) -> None:
        """Download file from MinIO to local path"""
        try:
            client = self._get_client()
            logger.debug("Downloading object %s from bucket %s to local path %s", object_name, self.bucket_name, file_path)
            client.fget_object(self.bucket_name, object_name, file_path)
            logger.info("Downloaded file from MinIO: %s -> %s", object_name, file_path)
        except S3Error as e:
            logger.error(
                "Failed to download file from MinIO: %s", str(e), exc_info=True
            )
            raise

    def download_bytes(self, object_name: str) -> bytes:
        """Download file from MinIO as bytes"""
        try:
            client = self._get_client()
            logger.debug("Downloading object %s from bucket %s as bytes", object_name, self.bucket_name)
            response = client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info("Downloaded bytes from MinIO: %s", object_name)
            return data
        except S3Error as e:
            logger.error(
                "Failed to download bytes from MinIO: %s", str(e), exc_info=True
            )
            raise

    def upload_json(
        self, data: Dict[str, Any] | List[Dict[str, Any]], object_name: str
    ) -> str:
        """Upload JSON data to MinIO"""
        logger.debug("Uploading JSON object %s", object_name)
        json_bytes = json.dumps(data, indent=2).encode("utf-8")
        return self.upload_bytes(
            json_bytes, object_name, content_type="application/json"
        )

    def download_json(self, object_name: str) -> Dict[str, Any] | List[Dict[str, Any]]:
        """Download and parse JSON from MinIO"""
        logger.debug("Downloading and parsing JSON object %s", object_name)
        data = self.download_bytes(object_name)
        result = json.loads(data.decode("utf-8"))
        logger.info("Downloaded and parsed JSON from object: %s", object_name)
        return result

    def delete_object(self, object_name: str) -> None:
        """Delete object from MinIO"""
        try:
            client = self._get_client()
            logger.debug("Deleting object %s from bucket %s", object_name, self.bucket_name)
            client.remove_object(self.bucket_name, object_name)
            logger.info("Deleted object from MinIO: %s", object_name)
        except S3Error as e:
            logger.error(
                "Failed to delete object from MinIO: %s", str(e), exc_info=True
            )
            raise

    def object_exists(self, object_name: str) -> bool:
        """Check if object exists in MinIO"""
        try:
            client = self._get_client()
            logger.debug("Checking existence of object %s in bucket %s", object_name, self.bucket_name)
            client.stat_object(self.bucket_name, object_name)
            logger.info("Object %s exists in bucket %s", object_name, self.bucket_name)
            return True
        except S3Error:
            logger.info("Object %s does not exist in bucket %s", object_name, self.bucket_name)
            return False

    def get_object_path(
        self, artifact_type: str, file_hash: str, extension: str = ""
    ) -> str:
        """Generate standardized object path"""
        logger.debug("Generating object path for artifact_type=%s, file_hash=%s, extension=%s", artifact_type, file_hash, extension)
        if artifact_type == "raw":
            return f"raw/{file_hash}{extension}"
        elif artifact_type == "extracted":
            return f"extracted/{file_hash}.json"
        elif artifact_type == "chunks":
            return f"chunks/{file_hash}.json"
        else:
            logger.error("Unknown artifact type: %s", artifact_type)
            raise ValueError(f"Unknown artifact type: {artifact_type}")