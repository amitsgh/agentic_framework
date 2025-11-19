"""Utility Functions"""

import hashlib
from pathlib import Path

from fastapi import UploadFile

from app.config import config
from app.exceptions import ValidationError
from app.utils.logger import setuplog

logger = setuplog(__name__)


def file_validation(file: UploadFile) -> None:
    """Validate uploaded file"""
    if not file.filename:
        raise ValidationError("No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in config.ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File extension {file_ext} not allowed. "
            f"Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"
        )

    if hasattr(file.file, "seek") and hasattr(file.file, "tell"):
        file.file.seek(0, 2)  # seek to end
        size = file.file.tell()
        file.file.seek(0)

        if size > config.MAX_UPLOAD_SIZE:
            raise ValidationError(
                f"File size {size} exceeds maximum {config.MAX_UPLOAD_SIZE} bytes"
            )


def compute_file_hash(file_path: str | Path, algorithm: str = "sha256") -> str:
    """Compute hash of a file"""

    hash_obj = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def compute_file_hash_from_bytes(file_bytes: bytes, algorithm: str = "sha256") -> str:
    """Compute hash from file bytes"""

    hash_obj = hashlib.new(algorithm)
    hash_obj.update(file_bytes)
    return hash_obj.hexdigest()
