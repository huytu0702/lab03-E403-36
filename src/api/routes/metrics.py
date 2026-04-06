from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from src.telemetry.trace_store import trace_store


router = APIRouter(prefix="/metrics", tags=["metrics"])


def _safe_mean(values: List[int | float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


@router.get("/summary")
def metrics_summary() -> Dict[str, Any]:
    traces = trace_store.list_traces()
    if not traces:
        return {"total_traces": 0, "success_rate": 0.0, "by_version": {}, "by_provider": {}}

    by_version: Dict[str, Any] = {}
    by_provider: Dict[str, Any] = {}
    total_success = 0

    for trace in traces:
        metrics = trace.get("metrics") or {}
        version = trace.get("version", "unknown")
        provider = metrics.get("provider") or "unknown"
        status = trace.get("status")
        total_success += int(status == "success")

        version_bucket = by_version.setdefault(
            version,
            {
                "count": 0,
                "success": 0,
                "error": 0,
                "latency_ms": [],
                "steps": [],
                "tool_calls_count": [],
                "prompt_tokens": [],
                "completion_tokens": [],
                "total_tokens": [],
                "llm_calls": [],
            },
        )
        provider_bucket = by_provider.setdefault(
            provider,
            {
                "count": 0,
                "latency_ms": [],
                "total_tokens": [],
                "llm_calls": [],
            },
        )

        version_bucket["count"] += 1
        provider_bucket["count"] += 1
        if status == "success":
            version_bucket["success"] += 1
        elif status == "error":
            version_bucket["error"] += 1

        token_usage = metrics.get("token_usage") or {}
        version_bucket["latency_ms"].append(int(metrics.get("latency_ms", 0)))
        version_bucket["steps"].append(int(metrics.get("steps", 0)))
        version_bucket["tool_calls_count"].append(int(metrics.get("tool_calls_count", 0)))
        version_bucket["prompt_tokens"].append(int(token_usage.get("prompt_tokens", 0)))
        version_bucket["completion_tokens"].append(int(token_usage.get("completion_tokens", 0)))
        version_bucket["total_tokens"].append(int(token_usage.get("total_tokens", 0)))
        version_bucket["llm_calls"].append(int(metrics.get("llm_calls", 0)))

        provider_bucket["latency_ms"].append(int(metrics.get("llm_latency_ms", 0)))
        provider_bucket["total_tokens"].append(int(token_usage.get("total_tokens", 0)))
        provider_bucket["llm_calls"].append(int(metrics.get("llm_calls", 0)))

    rendered_versions = {
        version: {
            "count": bucket["count"],
            "success_rate": round(bucket["success"] / bucket["count"], 3) if bucket["count"] else 0.0,
            "avg_latency_ms": _safe_mean(bucket["latency_ms"]),
            "avg_steps": _safe_mean(bucket["steps"]),
            "avg_tool_calls": _safe_mean(bucket["tool_calls_count"]),
            "avg_prompt_tokens": _safe_mean(bucket["prompt_tokens"]),
            "avg_completion_tokens": _safe_mean(bucket["completion_tokens"]),
            "avg_total_tokens": _safe_mean(bucket["total_tokens"]),
            "avg_llm_calls": _safe_mean(bucket["llm_calls"]),
        }
        for version, bucket in by_version.items()
    }
    rendered_providers = {
        provider: {
            "count": bucket["count"],
            "avg_llm_latency_ms": _safe_mean(bucket["latency_ms"]),
            "avg_total_tokens": _safe_mean(bucket["total_tokens"]),
            "avg_llm_calls": _safe_mean(bucket["llm_calls"]),
        }
        for provider, bucket in by_provider.items()
    }

    return {
        "total_traces": len(traces),
        "success_rate": round(total_success / len(traces), 3),
        "by_version": rendered_versions,
        "by_provider": rendered_providers,
    }
