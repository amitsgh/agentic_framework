# app/api/v1/documents.py
"""Document API routes - routes only"""
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, HTTPException, Depends, Query

from app.dependency import get_db_sync, get_embeddings, get_extractor, get_chunker, get_cache
from app.controllers.document_controller import DocumentController
from app.repositories.document_repository import DocumentRepository
from typing import Tuple
from app.utils.utils import file_validation, compute_file_hash_from_bytes
from app.pipeline.pipeline import DocumentPipeline
from app.manager.state_manager import StateManager
from app.models.document_model import DocumentResponse
from app.models.processing_state import ProcessingStage
from app.config import config
from app.exceptions import (
    DocumentProcessingError,
    DatabaseError,
    ValidationError,
)
from app.utils.logger import setuplog

logger = setuplog(__name__)

router = APIRouter()


def _create_document_controller(
    extractor=Depends(get_extractor),
    chunker=Depends(get_chunker),
    cache=Depends(get_cache),
) -> Tuple[type[DocumentController], DocumentPipeline, StateManager]:
    """Create document controller factory (without DB - DB managed in route)"""
    state_manager = StateManager(cache)
    pipeline = DocumentPipeline(extractor, chunker, state_manager)
    
    # Note: DB and repository will be created in the route handler to properly manage lifecycle
    # This is a factory that returns components needed to create controller with DB
    return DocumentController, pipeline, state_manager


def _generate_response_message(state, documents, file_hash: str) -> str:
    """Generate response message"""
    stage = state.stage
    num_chunks = len(documents)
    hash_short = file_hash[:16]
    
    if stage == ProcessingStage.STORED:
        return (
            f"Document processed and stored successfully. "
            f"Created {num_chunks} chunks. (Hash: {hash_short}...)"
        )
    elif stage == ProcessingStage.CHUNKED:
        return (
            f"Document extracted and chunked successfully. "
            f"Created {num_chunks} chunks. (Hash: {hash_short}...)"
        )
    elif stage == ProcessingStage.FAILED:
        error_msg = state.error_message or "Unknown error"
        return (
            f"Document processing failed. "
            f"Error: {error_msg[:100]}. (Hash: {hash_short}...)"
        )
    else:
        return (
            f"Document uploaded successfully. "
            f"Current stage: {stage.value}. (Hash: {hash_short}...)"
        )


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile,
    forced_reprocess: bool = Query(default=False),
    controller_factory=Depends(_create_document_controller),
    embeddings=Depends(get_embeddings),
    db=Depends(get_db_sync),
):
    """Upload and process document"""
    try:
        # Validate file
        file_validation(file)
        
        # Read file and compute hash
        file.file.seek(0)
        file_bytes = file.file.read()
        file.file.seek(0)
        file_hash = compute_file_hash_from_bytes(file_bytes)
        
        # Save file temporarily
        upload_dir = Path(config.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / Path(file.filename)  # type: ignore
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create controller with proper DB lifecycle management
        DocumentControllerClass, pipeline, state_manager = controller_factory
        for db_instance in db:
            document_repository = DocumentRepository(db_instance)
            controller = DocumentControllerClass(pipeline, state_manager, document_repository)
            
            # Process document
            documents, state = controller.upload(
                file_path=str(temp_path),
                file_hash=file_hash,
                embeddings=embeddings,
                forced_reprocess=forced_reprocess,
            )
            break  # Exit after first iteration to ensure cleanup
        
        # Generate response
        message = _generate_response_message(state, documents, file_hash)
        
        return DocumentResponse(
            status="success",
            file_name=file.filename,  # type: ignore
            message=message,
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DocumentProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error in upload_document")
        raise HTTPException(status_code=500, detail="An unexpected error occurred") from e


@router.delete("/delete-all")
async def delete_all_documents(
    controller_factory=Depends(_create_document_controller),
    db=Depends(get_db_sync),
):
    """Delete all documents from database"""
    try:
        # Create controller with proper DB lifecycle management
        DocumentControllerClass, pipeline, state_manager = controller_factory
        for db_instance in db:
            document_repository = DocumentRepository(db_instance)
            controller = DocumentControllerClass(pipeline, state_manager, document_repository)
            
            count = controller.delete_all()
            return DocumentResponse(
                status="success",
                file_name="",
                message=f"Successfully deleted {count} documents from database.",
            )
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error in delete_all_documents")
        raise HTTPException(status_code=500, detail="An unexpected error occurred") from e