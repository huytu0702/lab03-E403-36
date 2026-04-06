from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.agent.agent import agent
from src.chatbot.chatbot import chatbot
from src.core.config import get_settings
from src.schemas.api import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    settings = get_settings()
    version = (request.version or settings.version).lower()

    try:
        if version == "v2":
            result = agent.run(request.message, session_id=request.session_id)
        else:
            result = chatbot.run(request.message, session_id=request.session_id)
        return result
    except ValueError as exc:
        error_code = str(exc)
        return JSONResponse(
            status_code=400,
            content={
                "version": version,
                "answer": "Yêu cầu không hợp lệ.",
                "latency_ms": 0,
                "steps": 0,
                "tool_calls": [],
                "trace_id": "",
                "status": "error",
                "error_code": error_code,
            },
        )
