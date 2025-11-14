"""Utility Functions"""

import hashlib
from pathlib import Path
from typing import Optional


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