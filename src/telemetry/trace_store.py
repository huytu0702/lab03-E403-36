import json
import os
from datetime import datetime, timezone
from typing import Any, Dict


class TraceStore:
    def __init__(self, base_dir: str = "logs/traces"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

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
        path = os.path.join(self.base_dir, f"{trace['trace_id']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(trace, f, ensure_ascii=False, indent=2)
        return path

    def load(self, trace_id: str) -> Dict[str, Any]:
        path = os.path.join(self.base_dir, f"{trace_id}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


trace_store = TraceStore()
