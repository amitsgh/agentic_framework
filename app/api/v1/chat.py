"""API for Query -> Retrieval -> Prompting -> LLM Response"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.controllers.chat_controller import ChatController

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/chat")
def chat(query: str):
    """Endpoint for chat interaction"""

    try:
        controller = ChatController()
        stream = controller.chat_stream(query)

        return StreamingResponse(
            stream,
            media_type="text/plain",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
