from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.core.config import get_settings
from src.schemas.api import ChatRequest, ChatResponse
from src.services.chat_service import run_chat

router = APIRouter(tags=["chat"])


ERROR_ANSWERS = {
    "INVALID_VERSION": "Phiên bản chatbot không hợp lệ.",
}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    settings = get_settings()
    version = (request.version or settings.version).lower()

    try:
        result = run_chat(request.message, version=version, session_id=request.session_id)
        return result
    except ValueError as exc:
        error_code = str(exc)
        return JSONResponse(
            status_code=400,
            content={
                "version": version,
                "answer": ERROR_ANSWERS.get(error_code, "Yêu cầu không hợp lệ."),
                "latency_ms": 0,
                "steps": 0,
                "tool_calls": [],
                "reasoning_steps": [],
                "trace_id": "",
                "status": "error",
                "error_code": error_code,
                "provider": None,
                "model": None,
                "llm_calls": 0,
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "cost_estimate": 0.0,
                "compare_results": None,
            },
        )
