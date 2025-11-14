"""API to Ingest -> Parser -> Document -> Embed -> Store"""

import shutil
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, HTTPException, Depends

from app.dependency import (
    get_db_sync,
    get_embeddings,
    get_extractor,
    get_chunker,
    get_cache,
)
from app.controllers.database_controller import DatabaseController
from app.controllers.document_controller import DocumentController
from app.models.document_model import DocumentResponse
from app.models.processing_state import ProcessingStage
from app.core.utils.utils import compute_file_hash_from_bytes
from app.core.config import config
from app.core.exceptions.base import (
    DocumentProcessingError,
    DatabaseError,
    ValidationError,
)
from app.core.decorator.timer import timer
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


@timer
@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile,
    embeddings=Depends(get_embeddings),
    extractor=Depends(get_extractor),
    chunker=Depends(get_chunker),
    cache=Depends(get_cache),
    forced_reprocess: bool = False,
):
    """Endpoint to upload and process a files"""

    try:
        validate_file(file)

        if not file.filename:
            raise ValidationError("No filename provided")

        # read file to compute hash
        file.file.seek(0)
        file_bytes = file.file.read()
        file.file.seek(0)

        file_hash = compute_file_hash_from_bytes(file_bytes)
        logger.info(
            "File hash computed: %s for file: %s", file_hash[:16], file.filename
        )

        # check if already processed (unless force_reprocess)
        if not forced_reprocess and cache:
            state = cache.get(f"doc_state:{file_hash}")
            if state and state.get("stage") == ProcessingStage.STORED.value:
                logger.info("File already processed, skipping: %s", file.filename)
                return DocumentResponse(
                    status="success",
                    file_name=file.filename,
                    message="Document already processed. Use force_reprocess=true to reprocess.",
                )

        # save file temporary
        upload_dir = Path(config.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / Path(file.filename)

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        doc_controller = DocumentController(
            extractor=extractor, chunker=chunker, cache=cache
        )
        documents, state = doc_controller.create_documents(
            str(temp_path), file_hash=file_hash
        )

        # Step 3: Embed & Store
        if state.stage != ProcessingStage.STORED:
            try:
                db = next(get_db_sync())
                db_controller = DatabaseController(db=db)
                _ = db_controller.add_documents_to_db(documents, embeddings)

                state.stage = ProcessingStage.STORED
                state.updated_at = datetime.now(timezone.utc).isoformat()

                # Update cache with validation
                if cache:
                    success = cache.set(
                        f"doc_state:{file_hash}", state.model_dump(), ttl=86400 * 7
                    )
                    if not success:
                        logger.warning(
                            "Failed to update state in cache for file_hash: %s",
                            file_hash[:16],
                        )
                    else:
                        logger.info(
                            "Successfully updated state to STORED in cache for file_hash: %s",
                            file_hash[:16],
                        )

            except Exception as e:
                logger.error("Error storing documents: %s", str(e), exc_info=True)
                
                if cache:
                    state.stage = ProcessingStage.FAILED
                    state.error_message = str(e)
                    state.updated_at = datetime.now(timezone.utc).isoformat()
                    cache.set(
                        f"doc_state:{file_hash}", state.model_dump(), ttl=86400 * 7
                    )
                raise DatabaseError(f"Error storing documents: {str(e)}") from e

        return DocumentResponse(
            status="success",
            file_name=file.filename,
            message=f"Document processed successfully. Created {len(documents)} chunks. (Hash: {file_hash[:16]}...)",
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


@timer
@router.delete("/delete-all")
async def delete_all_documents():
    """Endpoint to delete all documents from the database"""

    try:
        db = next(get_db_sync())
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
