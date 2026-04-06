from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from fastapi import APIRouter


router = APIRouter(prefix="/metrics", tags=["metrics"])


def _safe_mean(values: List[int]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


@router.get("/summary")
def metrics_summary() -> Dict[str, Any]:
    """
    Summarize metrics from trace JSON files in logs/traces.
    """
    base_dir = "logs/traces"
    if not os.path.isdir(base_dir):
        return {"total_traces": 0, "by_version": {}}

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
    for tr in traces:
        version = tr.get("version", "unknown")
        by_version.setdefault(version, {"count": 0, "success": 0, "error": 0, "latencies_ms": [], "steps": []})
        bucket = by_version[version]
        bucket["count"] += 1
        status = tr.get("status")
        if status == "success":
            bucket["success"] += 1
        elif status == "error":
            bucket["error"] += 1
        metrics = tr.get("metrics") or {}
        if "latency_ms" in metrics:
            bucket["latencies_ms"].append(int(metrics["latency_ms"]))
        if "steps" in metrics:
            bucket["steps"].append(int(metrics["steps"]))

    rendered: Dict[str, Any] = {}
    for version, bucket in by_version.items():
        count = bucket["count"]
        rendered[version] = {
            "count": count,
            "success_rate": (bucket["success"] / count) if count else 0.0,
            "avg_latency_ms": _safe_mean(bucket["latencies_ms"]),
            "avg_steps": _safe_mean(bucket["steps"]),
        }

    return {"total_traces": len(traces), "by_version": rendered}

