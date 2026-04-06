from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from fastapi import APIRouter

from src.telemetry.metrics import tracker


router = APIRouter(prefix="/metrics", tags=["metrics"])


def _safe_mean(values: List[int]) -> float:
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
    """Summarize metrics from trace JSON files in `logs/traces` and live LLM usage."""
    base_dir = "logs/traces"
    if not os.path.isdir(base_dir):
        return {
            "total_traces": 0,
            "by_version": {},
            "recent_traces": [],
            "live_session_metrics": tracker.summary(),
        }

    traces: List[Dict[str, Any]] = []
    for name in os.listdir(base_dir):
        if not name.endswith(".json"):
            continue
        path = os.path.join(base_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                traces.append(json.load(f))
        except Exception:
            continue

    by_version: Dict[str, Any] = {}
    recent_traces: List[Dict[str, Any]] = []

    for trace in traces:
        version = trace.get("version", "unknown")
        by_version.setdefault(
            version,
            {
                "count": 0,
                "success": 0,
                "error": 0,
                "latencies_ms": [],
                "steps": [],
                "tool_calls": [],
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "providers": set(),
                "models": set(),
            },
        )
        bucket = by_version[version]
        bucket["count"] += 1

        status = trace.get("status")
        if status == "success":
            bucket["success"] += 1
        elif status == "error":
            bucket["error"] += 1

        metrics = trace.get("metrics") or {}
        bucket["latencies_ms"].append(_to_int(metrics.get("latency_ms")))
        bucket["steps"].append(_to_int(metrics.get("steps")))
        bucket["tool_calls"].append(_to_int(metrics.get("tool_calls_count")))
        bucket["prompt_tokens"] += _to_int(metrics.get("prompt_tokens"))
        bucket["completion_tokens"] += _to_int(metrics.get("completion_tokens"))
        bucket["total_tokens"] += _to_int(metrics.get("total_tokens"))

        provider = metrics.get("provider")
        model = metrics.get("model")
        if provider:
            bucket["providers"].add(provider)
        if model:
            bucket["models"].add(model)

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

    rendered: Dict[str, Any] = {}
    for version, bucket in by_version.items():
        count = bucket["count"]
        rendered[version] = {
            "count": count,
            "success_rate": round(bucket["success"] / count, 4) if count else 0.0,
            "avg_latency_ms": _safe_mean(bucket["latencies_ms"]),
            "avg_steps": _safe_mean(bucket["steps"]),
            "avg_tool_calls": _safe_mean(bucket["tool_calls"]),
            "total_tokens": bucket["total_tokens"],
            "avg_total_tokens": round(bucket["total_tokens"] / count, 2) if count else 0.0,
            "providers": sorted(bucket["providers"]),
            "models": sorted(bucket["models"]),
        }

    recent_traces.sort(key=lambda item: item.get("trace_id") or "", reverse=True)
    return {
        "total_traces": len(traces),
        "by_version": rendered,
        "recent_traces": recent_traces[:10],
        "live_session_metrics": tracker.summary(),
    }

