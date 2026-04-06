from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from src.telemetry.logger import logger


class PerformanceTracker:
    """Track request-level telemetry for local and external LLM providers."""

    def __init__(self):
        self.session_metrics: List[Dict[str, Any]] = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int] | None, latency_ms: int) -> Dict[str, Any]:
        usage = usage or {}
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
            "latency_ms": int(latency_ms or 0),
            "cost_estimate": self._calculate_cost(model, usage),
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

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        return round((int(usage.get("total_tokens", 0) or 0) / 1000) * 0.01, 6)


tracker = PerformanceTracker()
