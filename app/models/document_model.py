"""Model for Document"""

from typing import Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Model for Document BoundingBox"""

    l: Optional[float] = Field(None, description="Left coordinate.")
    t: Optional[float] = Field(None, description="Top coordinate.")
    r: Optional[float] = Field(None, description="Right coordinate.")
    b: Optional[float] = Field(None, description="Bottom coordinate.")
    coord_origin: Optional[str] = Field(
        None, description="Coordinate origin (e.g., 'BOTTOMLEFT')."
    )


class DocumentMetadata(BaseModel):
    """Model for Document Metadata"""

    source: Optional[str] = Field(
        None, description="Full path or URI of the original file."
    )
    filename: Optional[str] = Field(None, description="Name of the original file.")
    page_no: Optional[int] = Field(None, description="Page number of extracted text.")
    content_layer: Optional[str] = Field(
        None, description="Layer of document content (e.g., body, header)."
    )
    mimetype: Optional[str] = Field(None, description="MIME type of the source file.")
    binary_hash: Optional[int] = Field(
        None, description="Binary hash of the source file."
    )
    bbox: Optional[BoundingBox] = Field(
        None, description="Bounding box of the text region."
    )


class Document(BaseModel):
    """Model for Document Model"""

    content: str = Field(..., description="Extracted text content.")
    metadata: Optional[DocumentMetadata] = Field(
        None, description="Flattened metadata of the document content."
    )


class DocumentResponse(BaseModel):
    """Model for Document Response"""

    status: str = Field(
        ...,
        description="Result of the document operation (e.g., 'success' or 'error').",
    )
    file_name: str = Field(..., description="Name of the uploaded or processed file.")
    message: Optional[str] = Field(
        None, description="Additional information or error details."
    )
