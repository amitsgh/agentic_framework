"""API to Ingest -> Parser -> Document -> Embed -> Store"""

import shutil
from fastapi import APIRouter, UploadFile, HTTPException, Depends

from app.dependency import get_embeddings
from app.controllers.database_controller import DatabaseController
from app.controllers.document_controller import DocumentController
from app.models.document_model import DocumentResponse
from app.core.config import config


router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile, embeddings=Depends(get_embeddings)
):
    """Endpoint to upload and ingest a document"""

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = config.UPLOAD_DIR / file.filename

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        documents = DocumentController().create_documents(str(temp_path))
        _ = DatabaseController().add_documents_to_db(documents, embeddings)

        return DocumentResponse(
            status="success",
            file_name=file.filename,
            message="Document uploaded successfully. Processing in background",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing document: {str(e)}"
        )

@router.delete("/delete-all")
async def delete_all_documents():
    """Endpoint to delete all documents from the database"""

    try:
        count = DatabaseController().delete_all_documents()

        return DocumentResponse(
            status="success",
            file_name="",
            message=f"Successfully deleted {count} documents from the database",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting documents: {str(e)}"
        )
