from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    version: Optional[str] = None
    session_id: Optional[str] = None


class ToolCallSummary(BaseModel):
    tool: str
    args: Dict[str, Any]
    result_preview: str


class ChatResponse(BaseModel):
    version: str
    answer: str
    latency_ms: int
    steps: int
    tool_calls: List[ToolCallSummary]
    trace_id: str
    status: str
    error_code: Optional[str] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    trace_id: Optional[str] = None
