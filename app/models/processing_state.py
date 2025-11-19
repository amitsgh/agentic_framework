"""Processing State Models"""

from typing import Optional, List, Dict
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

    @classmethod
    def get_valid_transitions(cls) -> Dict[str, List[str]]:
        """Define valid stage transitions"""
        return {
            cls.UPLOADED: [cls.EXTRACTED, cls.FAILED],
            cls.EXTRACTED: [cls.CHUNKED, cls.FAILED],
            cls.CHUNKED: [cls.EMBEDDED, cls.FAILED],
            cls.EMBEDDED: [cls.STORED, cls.FAILED],
            cls.STORED: [],  # terminate state
            cls.FAILED: [],  # terminate state
        }

    def can_transition_to(self, target: "ProcessingStage") -> bool:
        """Check if transition to target stage is valid"""
        valid_next = self.get_valid_transitions().get(self.value, [])
        return target.value in valid_next


class ProcessingState(BaseModel):
    """Document processing state"""

    file_hash: str = Field(..., description="SHA256 hash of the file")
    filename: str = Field(..., description="Original filename")
    stage: ProcessingStage = Field(
        default=ProcessingStage.UPLOADED, description="Current processing stage"
    )

    # Artifact paths in MinIO
    artifact_paths: Dict[str, str] = Field(default_factory=dict)

    # Metadata
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[str] = Field(None, description="Processing start time")
    updated_at: Optional[str] = Field(None, description="Last update time")

    def get_artifact_path(self, artifact_type: str) -> Optional[str]:
        """Get path for a specific artifact type"""
        return dict(self.artifact_paths).get(artifact_type)

    def set_artifact_path(self, artifact_type: str, path: str) -> None:
        """Set path for a specific artifact type"""
        self.artifact_paths[artifact_type] = path
