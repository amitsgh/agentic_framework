"""API to Ingest -> Parser -> Document -> Embed -> Store"""

import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, HTTPException, Depends

from app.dependency import get_embeddings, get_extractor, get_chunker, get_db_sync
from app.controllers.database_controller import DatabaseController
from app.controllers.document_controller import DocumentController
from app.models.document_model import DocumentResponse
from app.core.config import config
from app.core.exceptions.base import (
    DocumentProcessingError,
    DatabaseError,
    ValidationError,
)
from app.core.logger import setuplog

logger = setuplog(__name__)

router = APIRouter()


def validate_file(file: UploadFile) -> None:
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


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile,
    embeddings=Depends(get_embeddings),
    extractor=Depends(get_extractor),
    chunker=Depends(get_chunker),
):
    """Endpoint to upload and process a files"""

    try:
        validate_file(file)

        if not file.filename:
            raise ValidationError("No filename provided")

        upload_dir = Path(config.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / Path(file.filename)

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        doc_controller = DocumentController(extractor=extractor, chunker=chunker)
        documents = doc_controller.create_documents(str(temp_path))

        for db in get_db_sync():
            db_controller = DatabaseController(db=db)
            _ = db_controller.add_documents_to_db(documents, embeddings)

        return DocumentResponse(
            status="success",
            file_name=file.filename,
            message=f"Document uploaded successfully. Created {len(documents)} chunks.",
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DocumentProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error in upload_document")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred"
        ) from e


@router.delete("/delete-all")
async def delete_all_documents():
    """Endpoint to delete all documents from the database"""

    try:
        for db in get_db_sync():
            db_controller = DatabaseController(db=db)
            count = db_controller.delete_all_documents()

            return DocumentResponse(
                status="success",
                file_name="",
                message=f"Successfully deleted {count} documents from the database",
            )

    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error in delete_all_documents")
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred"
        ) from e
