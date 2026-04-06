from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_healthcheck_reports_status_and_db_mode():
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"]["mode"] in {"postgres", "fallback-seed"}


def test_products_endpoint_returns_seed_or_db_catalog():
    response = client.get("/api/v1/products")
    assert response.status_code == 200

    payload = response.json()
    assert isinstance(payload, list)
    assert any(item["name"] == "iPhone 15" for item in payload)


def test_tool_stock_endpoint_checks_inventory():
    response = client.post(
        "/api/v1/tools/check-stock",
        json={"product_name": "MacBook Air M3", "quantity": 1},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["product_name"] == "MacBook Air M3"
    assert payload["in_stock"] is True


def test_invalid_coupon_returns_expected_error_code():
    response = client.post(
        "/api/v1/tools/get-coupon-discount",
        json={"coupon_code": "SAVE999", "order_subtotal": 10000000},
    )
    assert response.status_code == 404
    assert response.json()["error_code"] == "COUPON_NOT_FOUND"


def test_chat_v1_answers_faq_case():
    response = client.post(
        "/api/v1/chat",
        json={"message": "Chính sách đổi trả là gì?", "version": "v1", "session_id": "pytest-v1"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert "7 ngày" in payload["answer"]
    assert payload["steps"] == 1


def test_chat_v2_handles_multistep_quote_with_tool_calls():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Tôi muốn mua 2 iPhone 15, dùng mã WINNER10 và ship Hà Nội. Tổng bao nhiêu?",
            "version": "v2",
            "session_id": "pytest-v2",
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert payload["steps"] >= 2
    assert len(payload["tool_calls"]) >= 2
    assert "Tổng thanh toán dự kiến" in payload["answer"]


def test_metrics_summary_reflects_recent_requests():
    client.post(
        "/api/v1/chat",
        json={"message": "Shop có giao hàng cuối tuần không?", "version": "v1", "session_id": "pytest-metrics"},
    )

    response = client.get("/api/v1/metrics/summary")
    assert response.status_code == 200

    payload = response.json()
    assert "by_version" in payload
    assert "recent_traces" in payload
    assert payload["total_traces"] >= 1
