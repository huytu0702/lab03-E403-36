from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

<<<<<<< HEAD
from src.telemetry.metrics import tracker
=======
from src.telemetry.trace_store import trace_store
>>>>>>> 0c73add2950a3b23caf39caf4f34c4c2ea735a72


router = APIRouter(prefix="/metrics", tags=["metrics"])


def _safe_mean(values: List[int | float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)
<<<<<<< HEAD


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
=======
>>>>>>> 0c73add2950a3b23caf39caf4f34c4c2ea735a72


@router.get("/summary")
def metrics_summary() -> Dict[str, Any]:
<<<<<<< HEAD
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
=======
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
>>>>>>> 0c73add2950a3b23caf39caf4f34c4c2ea735a72
            version,
            {
                "count": 0,
                "success": 0,
                "error": 0,
<<<<<<< HEAD
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
=======
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
>>>>>>> 0c73add2950a3b23caf39caf4f34c4c2ea735a72
        if status == "success":
            version_bucket["success"] += 1
        elif status == "error":
<<<<<<< HEAD
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
=======
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
>>>>>>> 0c73add2950a3b23caf39caf4f34c4c2ea735a72
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

<<<<<<< HEAD
    recent_traces.sort(key=lambda item: item.get("trace_id") or "", reverse=True)
    return {
        "total_traces": len(traces),
        "by_version": rendered,
        "recent_traces": recent_traces[:10],
        "live_session_metrics": tracker.summary(),
    }

=======
    return {
        "total_traces": len(traces),
        "success_rate": round(total_success / len(traces), 3),
        "by_version": rendered_versions,
        "by_provider": rendered_providers,
    }
>>>>>>> 0c73add2950a3b23caf39caf4f34c4c2ea735a72
