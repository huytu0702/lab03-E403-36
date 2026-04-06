from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.api.main import app
from src.core.text import normalize_text


TEST_CASES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "FAQ đổi trả",
        "type": "chatbot-win",
        "input": "Chính sách đổi trả là gì?",
        "expected_keywords": ["7 ngay", "doi tra"],
    },
    {
        "id": 2,
        "name": "FAQ giao hàng cuối tuần",
        "type": "chatbot-win",
        "input": "Shop có giao hàng cuối tuần không?",
        "expected_keywords": ["cuoi tuan", "ha noi"],
    },
    {
        "id": 3,
        "name": "Quote nhiều bước",
        "type": "agent-win",
        "input": "Tôi muốn mua 2 iPhone 15, dùng mã WINNER10 và ship Hà Nội. Tổng bao nhiêu?",
        "expected_keywords": ["iphone 15", "tong thanh toan"],
    },
    {
        "id": 4,
        "name": "Kiểm tra hàng và tổng giá",
        "type": "agent-win",
        "input": "MacBook Air M3 còn hàng không? Nếu mua 1 cái ship TP.HCM thì hết bao nhiêu?",
        "expected_keywords": ["macbook air m3", "phi ship"],
    },
    {
        "id": 5,
        "name": "Edge case coupon sai",
        "type": "edge",
        "input": "Mua 3 AirPods Pro 2 dùng mã SAVE999 ship Đà Nẵng.",
        "expected_keywords": ["khong hop le"],
    },
]


def run_case(client: TestClient, version: str, prompt: str) -> Dict[str, Any]:
    response = client.post(
        "/api/v1/chat",
        json={"message": prompt, "version": version, "session_id": f"benchmark-{version}"},
    )
    payload = response.json()
    payload["http_status"] = response.status_code
    return payload


def evaluate_answer(case: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    normalized_answer = normalize_text(result.get("answer", ""))
    matched = all(keyword in normalized_answer for keyword in case["expected_keywords"])
    return {
        "status": result.get("status"),
        "latency_ms": result.get("latency_ms", 0),
        "steps": result.get("steps", 0),
        "tool_calls_count": len(result.get("tool_calls", [])),
        "matched_expected": matched,
        "trace_id": result.get("trace_id"),
        "answer": result.get("answer", ""),
        "error_code": result.get("error_code"),
    }


def pick_winner(case: Dict[str, Any], v1: Dict[str, Any], v2: Dict[str, Any]) -> str:
    if case["type"] == "chatbot-win":
        if v1["matched_expected"] and v2["matched_expected"]:
            return "v1"
        if v1["matched_expected"]:
            return "v1"
        if v2["matched_expected"]:
            return "v2"
    elif case["type"] == "agent-win":
        if v2["matched_expected"] and (v2["tool_calls_count"] > 0 or not v1["matched_expected"]):
            return "v2"
        if v1["matched_expected"] and v2["matched_expected"]:
            return "v2"
    else:
        if v2["matched_expected"] and not v1["matched_expected"]:
            return "v2"
        if v1["matched_expected"] and not v2["matched_expected"]:
            return "v1"

    if v1["matched_expected"] and v2["matched_expected"]:
        return "tie"
    if v2["matched_expected"]:
        return "v2"
    if v1["matched_expected"]:
        return "v1"
    return "needs-review"


def main() -> None:
    client = TestClient(app)
    results: List[Dict[str, Any]] = []

    for case in TEST_CASES:
        raw_v1 = run_case(client, "v1", case["input"])
        raw_v2 = run_case(client, "v2", case["input"])
        eval_v1 = evaluate_answer(case, raw_v1)
        eval_v2 = evaluate_answer(case, raw_v2)
        winner = pick_winner(case, eval_v1, eval_v2)
        results.append(
            {
                "case": case["id"],
                "name": case["name"],
                "type": case["type"],
                "input": case["input"],
                "winner": winner,
                "v1": eval_v1,
                "v2": eval_v2,
            }
        )

    output_dir = Path("logs/benchmarks")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "benchmark_latest.json"
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== Benchmark Summary ===")
    print(f"Saved detailed report to: {output_path}")
    print("| Case | Type | Winner | v1 matched | v2 matched |")
    print("| --- | --- | --- | --- | --- |")
    for item in results:
        print(
            f"| {item['case']} | {item['type']} | {item['winner']} | "
            f"{item['v1']['matched_expected']} | {item['v2']['matched_expected']} |"
        )


if __name__ == "__main__":
    main()
