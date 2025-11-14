"""Processing State Models"""

from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field


class ProcessingStage(str, Enum):
    """Processing stages"""

    UPLOADED = "uploaded"
    EXTRACTED = "extracted"
    CHUNKED = "chunked"
    EMBEDDED = "embedded"
    STORED = "stored"
    FAILED = "failed"


class ProcessingState(BaseModel):
    """Document processing state"""

    file_hash: str = Field(..., description="SHA256 hash of the file")
    filename: str = Field(..., description="Original filename")
    file_path: Optional[str] = Field(None, description="Temporary file path")
    stage: ProcessingStage = Field(
        default=ProcessingStage.UPLOADED, description="Current processing stage"
    )

    # Cached results
    extracted_docs: Optional[List[Dict[str, Any]]] = Field(
        None, description="Serialized extracted documents"
    )
    chunked_docs: Optional[List[Dict[str, Any]]] = Field(
        None, description="Serialized chunked documents"
    )

    # Metadata
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[str] = Field(None, description="Processing start time")
    updated_at: Optional[str] = Field(None, description="Last update time")
