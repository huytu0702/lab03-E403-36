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


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatRunResult(BaseModel):
    version: str
    answer: str
    latency_ms: int
    steps: int
    tool_calls: List[ToolCallSummary]
    reasoning_steps: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: str
    status: str
    error_code: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    llm_calls: int = 0
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    cost_estimate: float = 0.0


class ChatResponse(ChatRunResult):
    compare_results: Optional[Dict[str, ChatRunResult]] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    trace_id: Optional[str] = None
