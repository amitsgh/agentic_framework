"""API for Query -> Retrieval -> Prompting -> LLM Response"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse

from app.controllers.chat_controller import ChatController
from app.dependency import get_llm, get_db_sync, get_embeddings
from app.core.exceptions.base import LLMError, ValidationError, ConfigurationError
from app.core.config import config
from app.core.logger import setuplog

logger = setuplog(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/chat")
def chat(
    query: str = Query(..., min_length=1, description="User query"),
    model_name: str = Query(default="ollama/llama2", description="LLM model name"),
    use_rag: bool = Query(default=None, description="Enable RAG (overrides config)"),
):
    """Endpoint for chat interaction with optional RAG"""

    logger.info("Chat request received: query length=%d, model=%s", len(query), model_name)
    logger.debug("Chat parameters: query=%s, model_name=%s, use_rag=%s", 
                query[:50] if len(query) > 50 else query, model_name, use_rag)
    
    if not query or not query.strip():
        logger.warning("Empty query received in chat endpoint")
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        logger.debug("Getting LLM instance for model: %s", model_name)
        llm = get_llm(model_name)
        enable_rag = use_rag if use_rag is not None else config.RAG_ENABLED
        logger.debug("RAG enabled: %s", enable_rag)

        if enable_rag:
            logger.debug("RAG mode: initializing embeddings and database...")
            embeddings = get_embeddings()
            for db in get_db_sync():
                controller = ChatController(llm=llm, db=db, embeddings=embeddings)
                logger.debug("ChatController created with RAG enabled")
                stream = controller.chat_stream(query)
                return StreamingResponse(
                    stream,
                    media_type="text/plain",
                )
        else:
            logger.debug("Direct mode: creating ChatController without RAG...")
            controller = ChatController(llm=llm)
            stream = controller.chat_stream(query)
            return StreamingResponse(
                stream,
                media_type="text/plain",
            )

    except ValidationError as e:
        logger.warning("Validation error in chat: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except LLMError as e:
        logger.error("LLM error in chat: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
    except ConfigurationError as e:
        logger.critical("Configuration error in chat: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.critical("Unexpected error in chat: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred"
        ) from e
