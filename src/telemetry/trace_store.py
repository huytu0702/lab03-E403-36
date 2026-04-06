import json
import os
from datetime import datetime, timezone
from typing import Any, Dict


class TraceStore:
    def __init__(self, base_dir: str = "logs/traces"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _trace_path(self, trace_id: str) -> str:
        return os.path.join(self.base_dir, f"{trace_id}.json")

    def create_trace(self, version: str, user_query: str, session_id: str | None = None) -> Dict[str, Any]:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        return {
            "trace_id": f"trace_{timestamp}",
            "version": version,
            "session_id": session_id,
            "user_query": user_query,
            "status": "running",
            "steps": [],
            "metrics": {},
        }

    def append_step(self, trace: Dict[str, Any], step: Dict[str, Any]) -> None:
        trace["steps"].append(step)

    def finalize_trace(
        self,
        trace: Dict[str, Any],
        *,
        final_answer: str,
        status: str,
        metrics: Dict[str, Any],
        error_code: str | None = None,
    ) -> Dict[str, Any]:
        trace["final_answer"] = final_answer
        trace["status"] = status
        trace["metrics"] = metrics
        trace["error_code"] = error_code
        self.save(trace)
        return trace

    def save(self, trace: Dict[str, Any]) -> str:
        path = self._trace_path(trace["trace_id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(trace, f, ensure_ascii=False, indent=2)
        return path

    def load(self, trace_id: str) -> Dict[str, Any]:
        path = self._trace_path(trace_id)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_traces(self) -> list[Dict[str, Any]]:
        if not os.path.isdir(self.base_dir):
            return []

        traces: list[Dict[str, Any]] = []
        for name in sorted(os.listdir(self.base_dir)):
            if not name.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.base_dir, name), "r", encoding="utf-8") as f:
                    traces.append(json.load(f))
            except Exception:
                continue
        return traces


trace_store = TraceStore()
