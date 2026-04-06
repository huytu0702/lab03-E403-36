from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from src.telemetry.metrics import tracker
from src.telemetry.trace_store import trace_store


router = APIRouter(prefix="/metrics", tags=["metrics"])


def _safe_mean(values: List[int | float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


@router.get("/summary")
def metrics_summary() -> Dict[str, Any]:
    traces = trace_store.list_traces()
    if not traces:
        return {
            "total_traces": 0,
            "success_rate": 0.0,
            "by_version": {},
            "by_provider": {},
            "recent_traces": [],
            "live_session_metrics": tracker.summary(),
        }

    by_version: Dict[str, Any] = {}
    by_provider: Dict[str, Any] = {}
    recent_traces: List[Dict[str, Any]] = []
    total_success = 0

    for trace in traces:
        metrics = trace.get("metrics") or {}
        token_usage = metrics.get("token_usage") or {}
        version = trace.get("version", "unknown")
        provider = metrics.get("provider") or "unknown"
        model = metrics.get("model")
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
                "prompt_tokens_total": 0,
                "completion_tokens_total": 0,
                "total_tokens_total": 0,
                "llm_calls": [],
                "providers": set(),
                "models": set(),
            },
        )
        provider_bucket = by_provider.setdefault(
            provider,
            {
                "count": 0,
                "llm_latency_ms": [],
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

        version_bucket["latency_ms"].append(_to_int(metrics.get("latency_ms")))
        version_bucket["steps"].append(_to_int(metrics.get("steps")))
        version_bucket["tool_calls_count"].append(_to_int(metrics.get("tool_calls_count")))
        version_bucket["prompt_tokens_total"] += _to_int(token_usage.get("prompt_tokens", metrics.get("prompt_tokens")))
        version_bucket["completion_tokens_total"] += _to_int(
            token_usage.get("completion_tokens", metrics.get("completion_tokens"))
        )
        version_bucket["total_tokens_total"] += _to_int(token_usage.get("total_tokens", metrics.get("total_tokens")))
        version_bucket["llm_calls"].append(_to_int(metrics.get("llm_calls")))
        if provider:
            version_bucket["providers"].add(provider)
        if model:
            version_bucket["models"].add(model)

        provider_bucket["llm_latency_ms"].append(_to_int(metrics.get("llm_latency_ms", metrics.get("latency_ms"))))
        provider_bucket["total_tokens"].append(_to_int(token_usage.get("total_tokens", metrics.get("total_tokens"))))
        provider_bucket["llm_calls"].append(_to_int(metrics.get("llm_calls")))

        recent_traces.append(
            {
                "trace_id": trace.get("trace_id"),
                "version": version,
                "status": status,
                "user_query": trace.get("user_query"),
                "latency_ms": _to_int(metrics.get("latency_ms")),
                "steps": _to_int(metrics.get("steps")),
                "tool_calls_count": _to_int(metrics.get("tool_calls_count")),
                "error_code": trace.get("error_code"),
            }
        )

    rendered_versions = {}
    for version, bucket in by_version.items():
        count = bucket["count"]
        rendered_versions[version] = {
            "count": count,
            "success_rate": round(bucket["success"] / count, 4) if count else 0.0,
            "avg_latency_ms": _safe_mean(bucket["latency_ms"]),
            "avg_steps": _safe_mean(bucket["steps"]),
            "avg_tool_calls": _safe_mean(bucket["tool_calls_count"]),
            "total_tokens": bucket["total_tokens_total"],
            "avg_prompt_tokens": round(bucket["prompt_tokens_total"] / count, 2) if count else 0.0,
            "avg_completion_tokens": round(bucket["completion_tokens_total"] / count, 2) if count else 0.0,
            "avg_total_tokens": round(bucket["total_tokens_total"] / count, 2) if count else 0.0,
            "avg_llm_calls": _safe_mean(bucket["llm_calls"]),
            "providers": sorted(bucket["providers"]),
            "models": sorted(bucket["models"]),
        }

    rendered_providers = {
        provider: {
            "count": bucket["count"],
            "avg_llm_latency_ms": _safe_mean(bucket["llm_latency_ms"]),
            "avg_total_tokens": _safe_mean(bucket["total_tokens"]),
            "avg_llm_calls": _safe_mean(bucket["llm_calls"]),
        }
        for provider, bucket in by_provider.items()
    }

    recent_traces.sort(key=lambda item: item.get("trace_id") or "", reverse=True)
    return {
        "total_traces": len(traces),
        "success_rate": round(total_success / len(traces), 3),
        "by_version": rendered_versions,
        "by_provider": rendered_providers,
        "recent_traces": recent_traces[:10],
        "live_session_metrics": tracker.summary(),
    }
