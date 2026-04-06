from typing import Any, Dict

from src.telemetry.logger import logger


def normalize_usage(usage: Dict[str, int] | None = None) -> Dict[str, int]:
    usage = usage or {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens", 0)),
        "completion_tokens": int(usage.get("completion_tokens", 0)),
        "total_tokens": int(usage.get("total_tokens", 0)),
    }


class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """

    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to our telemetry.
        """
        normalized_usage = normalize_usage(usage)
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": normalized_usage["prompt_tokens"],
            "completion_tokens": normalized_usage["completion_tokens"],
            "total_tokens": normalized_usage["total_tokens"],
            "latency_ms": latency_ms,
            "cost_estimate": self.estimate_cost(model, normalized_usage),
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def estimate_cost(self, model: str, usage: Dict[str, int]) -> float:
        return (usage.get("total_tokens", 0) / 1000) * 0.01


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
