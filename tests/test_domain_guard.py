from __future__ import annotations


def test_v1_blocks_out_of_domain_question(client):
    response = client.post("/api/v1/chat", json={"message": "Thời tiết hôm nay thế nào?", "version": "v1"})
    assert response.status_code == 200

    data = response.json()
    assert data["error_code"] == "OUT_OF_DOMAIN"
    assert data["status"] == "blocked"
    assert "cửa hàng điện tử" in data["answer"]


def test_v2_blocks_out_of_domain_question(client):
    response = client.post("/api/v1/chat", json={"message": "Giải thích định luật Newton", "version": "v2"})
    assert response.status_code == 200

    data = response.json()
    assert data["error_code"] == "OUT_OF_DOMAIN"
    assert data["status"] == "blocked"


def test_compare_blocks_out_of_domain_question_before_running_both_versions(client):
    response = client.post("/api/v1/chat", json={"message": "Ai là tổng thống Mỹ?", "version": "compare"})
    assert response.status_code == 200

    data = response.json()
    assert data["error_code"] == "OUT_OF_DOMAIN"
    assert data["status"] == "blocked"
    assert data["compare_results"] is None


def test_domain_guard_still_allows_ecommerce_queries(client):
    response = client.post(
        "/api/v1/chat",
        json={"message": "MacBook Air M3 còn hàng không? Nếu mua 1 cái ship TP.HCM thì hết bao nhiêu?", "version": "v2"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
