# app/api/v1/chat.py
"""Chat API routes - routes only"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.dependency import get_llm, get_db_sync, get_embeddings
from app.controllers.chat_controller import ChatController
from app.repositories.document_repository import DocumentRepository
from app.config import config
from app.exceptions import LLMError, ValidationError, ConfigurationError
from app.utils.logger import setuplog

logger = setuplog(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/chat")
def chat(
    query: str = Query(..., min_length=1, description="User query"),
    model_name: str = Query(default="ollama/llama2", description="LLM model name"),
    use_rag: bool = Query(default=None, description="Enable RAG (overrides config)"),
):
    """Chat endpoint with optional RAG"""
    try:
        llm = get_llm(model_name)
        enable_rag = use_rag if use_rag is not None else config.RAG_ENABLED
        
        if enable_rag:
            embeddings = get_embeddings()
            for db in get_db_sync():
                document_repository = DocumentRepository(db)
                controller = ChatController(
                    llm=llm, document_repository=document_repository, embeddings=embeddings, use_rag=True
                )
                return StreamingResponse(
                    controller.chat_stream(query),
                    media_type="text/plain",
                )
        else:
            controller = ChatController(llm=llm, use_rag=False)
            return StreamingResponse(
                controller.chat_stream(query),
                media_type="text/plain",
            )
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except ConfigurationError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected error in chat")
        raise HTTPException(status_code=500, detail="An unexpected error occurred") from e