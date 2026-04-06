def test_tool_endpoints_success(client):
    price_response = client.post("/api/v1/tools/get-product-price", json={"product_name": "iPhone 15"})
    assert price_response.status_code == 200
    assert price_response.json()["unit_price"] == 24990000

    stock_response = client.post("/api/v1/tools/check-stock", json={"product_name": "iPhone 15", "quantity": 2})
    assert stock_response.status_code == 200
    assert stock_response.json()["in_stock"] is True

    coupon_response = client.post(
        "/api/v1/tools/get-coupon-discount",
        json={"coupon_code": "WINNER10", "order_subtotal": 49980000},
    )
    assert coupon_response.status_code == 200
    assert coupon_response.json()["discount_amount"] == 3000000

    shipping_response = client.post(
        "/api/v1/tools/calc-shipping",
        json={"destination_city": "Hà Nội", "total_weight_kg": 1.0},
    )
    assert shipping_response.status_code == 200
    assert shipping_response.json()["shipping_fee"] == 40000

    shipping_ascii_response = client.post(
        "/api/v1/tools/calc-shipping",
        json={"destination_city": "Ha Noi", "total_weight_kg": 1.0},
    )
    assert shipping_ascii_response.status_code == 200
    assert shipping_ascii_response.json()["shipping_fee"] == 40000


def test_tool_endpoints_edge_cases(client):
    coupon_response = client.post(
        "/api/v1/tools/get-coupon-discount",
        json={"coupon_code": "SAVE999", "order_subtotal": 16470000},
    )
    assert coupon_response.status_code == 404
    assert coupon_response.json()["error_code"] == "COUPON_NOT_FOUND"

    shipping_response = client.post(
        "/api/v1/tools/calc-shipping",
        json={"destination_city": "Huế", "total_weight_kg": 1.0},
    )
    assert shipping_response.status_code == 404
    assert shipping_response.json()["error_code"] == "SHIPPING_RULE_NOT_FOUND"

    product_response = client.post("/api/v1/tools/get-product-price", json={"product_name": "Pixel 9"})
    assert product_response.status_code == 404
    assert product_response.json()["error_code"] == "PRODUCT_NOT_FOUND"
