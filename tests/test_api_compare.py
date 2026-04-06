from __future__ import annotations

from pathlib import Path

from src.evaluation.benchmark_runner import run_benchmark_suite


def test_compare_chat_returns_v1_and_v2(client):
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Tôi muốn mua 2 iPhone 15, dùng mã WINNER10 và ship Hà Nội. Tổng bao nhiêu?",
            "version": "compare",
            "session_id": "pytest-compare",
        },
    )
    assert response.status_code == 200

    data = response.json()
    assert data["version"] == "compare"
    assert set(data["compare_results"].keys()) == {"v1", "v2"}
    assert data["compare_results"]["v1"]["reasoning_steps"]
    assert data["compare_results"]["v2"]["reasoning_steps"]
    assert "iPhone 15" in data["compare_results"]["v1"]["answer"]
    assert "Tổng thanh toán dự kiến" in data["compare_results"]["v2"]["answer"]


def test_metrics_summary_includes_version_and_provider_breakdowns(client):
    client.post("/api/v1/chat", json={"message": "Chính sách đổi trả là gì?", "version": "v1"})
    client.post(
        "/api/v1/chat",
        json={"message": "MacBook Air M3 còn hàng không? Nếu mua 1 cái ship TP.HCM thì hết bao nhiêu?", "version": "v2"},
    )

    response = client.get("/api/v1/metrics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_traces"] >= 2
    assert "v1" in data["by_version"]
    assert "v2" in data["by_version"]
    assert "mock" in data["by_provider"]
    assert "avg_total_tokens" in data["by_version"]["v2"]


def test_benchmark_suite_writes_expected_vs_actual_file(client, tmp_path):
    output_dir = tmp_path / "benchmarks"
    result = run_benchmark_suite(output_dir=str(output_dir))
    assert result["case_count"] == 5
    assert all("expected" in case for case in result["cases"])
    assert all("v1" in case and "v2" in case for case in result["cases"])
