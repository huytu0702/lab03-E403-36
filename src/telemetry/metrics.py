from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from src.telemetry.logger import logger


def normalize_usage(usage: Dict[str, int] | None = None) -> Dict[str, int]:
    usage = usage or {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
    }


class PerformanceTracker:
    """Track request-level telemetry for local and external LLM providers."""

    def __init__(self) -> None:
        self.session_metrics: List[Dict[str, Any]] = []

    def track_request(
        self,
        provider: str,
        model: str,
        usage: Dict[str, int] | None,
        latency_ms: int,
    ) -> Dict[str, Any]:
        normalized_usage = normalize_usage(usage)
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": normalized_usage["prompt_tokens"],
            "completion_tokens": normalized_usage["completion_tokens"],
            "total_tokens": normalized_usage["total_tokens"],
            "latency_ms": int(latency_ms or 0),
            "cost_estimate": self.estimate_cost(model, normalized_usage),
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)
        return metric

    def summary(self) -> Dict[str, Any]:
        if not self.session_metrics:
            return {"total_requests": 0, "by_provider": {}}

        by_provider: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "total_tokens": 0, "latency_ms": [], "models": set()}
        )
        for metric in self.session_metrics:
            bucket = by_provider[metric["provider"]]
            bucket["count"] += 1
            bucket["total_tokens"] += metric["total_tokens"]
            bucket["latency_ms"].append(metric["latency_ms"])
            bucket["models"].add(metric["model"])

        rendered: Dict[str, Any] = {}
        for provider, bucket in by_provider.items():
            count = bucket["count"]
            rendered[provider] = {
                "count": count,
                "avg_latency_ms": round(sum(bucket["latency_ms"]) / count, 2) if count else 0.0,
                "total_tokens": bucket["total_tokens"],
                "models": sorted(bucket["models"]),
            }

        return {"total_requests": len(self.session_metrics), "by_provider": rendered}

    def estimate_cost(self, model: str, usage: Dict[str, int]) -> float:
        return round((usage.get("total_tokens", 0) / 1000) * 0.01, 6)


def build_llm_metrics(
    *,
    provider: str | None,
    model: str | None,
    usage: Dict[str, int] | None,
    llm_calls: int,
    latency_ms: int,
) -> Dict[str, Any]:
    normalized_usage = normalize_usage(usage)
    return {
        "provider": provider,
        "model": model,
        "llm_calls": int(llm_calls),
        "token_usage": normalized_usage,
        "cost_estimate": tracker.estimate_cost(model or "unknown", normalized_usage),
        "llm_latency_ms": int(latency_ms),
    }


tracker = PerformanceTracker()
