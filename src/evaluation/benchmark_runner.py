from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.evaluation.benchmark_cases import AUXILIARY_CASES, BENCHMARK_CASES
from src.services.chat_service import run_chat, run_compare


def run_benchmark_suite(output_dir: str = "logs/benchmarks") -> Dict[str, Any]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    for case in BENCHMARK_CASES:
        result = run_compare(case["message"], session_id=f"benchmark-{case['id']}")
        v1 = result["compare_results"]["v1"]
        v2 = result["compare_results"]["v2"]
        rows.append(
            {
                "case_id": case["id"],
                "title": case["title"],
                "message": case["message"],
                "expected": case["expected"],
                "expected_winner": case["expected_winner"],
                "actual_winner": _recommend_winner(v1, v2, case["expected_winner"]),
                "v1": _summarize_result(v1),
                "v2": _summarize_result(v2),
            }
        )

    auxiliary_rows: List[Dict[str, Any]] = []
    for case in AUXILIARY_CASES:
        result = run_chat(case["message"], version="v1", session_id=f"benchmark-{case['id']}")
        auxiliary_rows.append(
            {
                "case_id": case["id"],
                "title": case["title"],
                "message": case["message"],
                "expected": case["expected"],
                "expected_status": case["expected_status"],
                "expected_error_code": case["expected_error_code"],
                "matches_expectation": _matches_auxiliary_expectation(result, case),
                "result": _summarize_result(result),
            }
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(rows),
        "auxiliary_case_count": len(auxiliary_rows),
        "cases": rows,
        "auxiliary_cases": auxiliary_rows,
    }
    filename = Path(output_dir) / f"benchmark_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with filename.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def _summarize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": result.get("status"),
        "answer": result.get("answer"),
        "latency_ms": result.get("latency_ms", 0),
        "steps": result.get("steps", 0),
        "tool_calls_count": len(result.get("tool_calls", [])),
        "trace_id": result.get("trace_id", ""),
        "error_code": result.get("error_code"),
        "token_usage": result.get("token_usage", {}),
    }


def _recommend_winner(v1: Dict[str, Any], v2: Dict[str, Any], expected_winner: str) -> str:
    v1_success = v1.get("status") == "success"
    v2_success = v2.get("status") == "success"
    if v1_success and not v2_success:
        return "v1"
    if v2_success and not v1_success:
        return "v2"
    if not v1_success and not v2_success:
        return "review"
    if expected_winner == "v2" and len(v2.get("tool_calls", [])) > 0:
        return "v2"
    if expected_winner == "v1" and v1.get("latency_ms", 0) <= v2.get("latency_ms", 0):
        return "v1"
    return "review"


def _matches_auxiliary_expectation(result: Dict[str, Any], case: Dict[str, Any]) -> bool:
    return (
        result.get("status") == case["expected_status"]
        and result.get("error_code") == case["expected_error_code"]
        and len(result.get("tool_calls", [])) == 0
        and int(result.get("llm_calls", 0)) == 0
        and int(result.get("token_usage", {}).get("total_tokens", 0)) == 0
    )
