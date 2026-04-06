from __future__ import annotations

import time
from typing import Any, Dict

from src.agent.agent import agent
from src.chatbot.chatbot import chatbot
from src.services.domain_guard import domain_guard


def run_chat(message: str, version: str, session_id: str | None = None) -> Dict[str, Any]:
    normalized_version = (version or "v1").lower()
    if normalized_version not in {"compare", "both", "v1", "v2"}:
        raise ValueError("INVALID_VERSION")
    if not domain_guard.is_in_domain(message):
        return build_out_of_domain_response(normalized_version)
    if normalized_version in {"compare", "both"}:
        return run_compare(message, session_id=session_id)
    if normalized_version == "v1":
        return chatbot.run(message, session_id=session_id)
    if normalized_version == "v2":
        return agent.run(message, session_id=session_id)
    raise ValueError("INVALID_VERSION")


def build_out_of_domain_response(version: str) -> Dict[str, Any]:
    return {
        "version": version,
        "answer": domain_guard.rejection_message(),
        "latency_ms": 0,
        "steps": 0,
        "tool_calls": [],
        "reasoning_steps": [],
        "trace_id": "",
        "status": "blocked",
        "error_code": "OUT_OF_DOMAIN",
        "provider": None,
        "model": None,
        "llm_calls": 0,
        "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "cost_estimate": 0.0,
        "compare_results": None,
    }


def run_compare(message: str, session_id: str | None = None) -> Dict[str, Any]:
    started_at = time.time()
    results = {
        "v1": chatbot.run(message, session_id=session_id),
        "v2": agent.run(message, session_id=session_id),
    }
    latency_ms = int((time.time() - started_at) * 1000)
    total_usage = {
        "prompt_tokens": sum(result.get("token_usage", {}).get("prompt_tokens", 0) for result in results.values()),
        "completion_tokens": sum(
            result.get("token_usage", {}).get("completion_tokens", 0) for result in results.values()
        ),
        "total_tokens": sum(result.get("token_usage", {}).get("total_tokens", 0) for result in results.values()),
    }
    tool_calls = [
        {"tool": call["tool"], "args": call["args"], "result_preview": f"[{version}] {call['result_preview']}"}
        for version, result in results.items()
        for call in result.get("tool_calls", [])
    ]

    success_count = sum(1 for result in results.values() if result.get("status") == "success")
    if success_count == len(results):
        status = "success"
        error_code = None
    elif success_count > 0:
        status = "partial_success"
        error_code = "COMPARE_PARTIAL_FAILURE"
    else:
        status = "error"
        error_code = "COMPARE_FAILED"

    answer = "\n\n".join(f"{version.upper()}:\n{result.get('answer', '')}" for version, result in results.items())
    return {
        "version": "compare",
        "answer": answer,
        "latency_ms": latency_ms,
        "steps": sum(result.get("steps", 0) for result in results.values()),
        "tool_calls": tool_calls,
        "reasoning_steps": [
            {"version": version, "steps": result.get("reasoning_steps", [])} for version, result in results.items()
        ],
        "trace_id": "",
        "status": status,
        "error_code": error_code,
        "provider": None,
        "model": None,
        "llm_calls": sum(result.get("llm_calls", 0) for result in results.values()),
        "token_usage": total_usage,
        "cost_estimate": sum(result.get("cost_estimate", 0.0) for result in results.values()),
        "compare_results": results,
    }
