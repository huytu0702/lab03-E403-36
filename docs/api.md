# API Design

## Mục tiêu

API phải phục vụ 3 nhóm nhu cầu:

- frontend chat UI
- tool execution cho `v2`
- tra cứu dữ liệu cho debug và demo

## Base URL

```text
/api/v1
```

## 1. Chat API

### `POST /api/v1/chat`

Endpoint chung cho cả `v1` và `v2`.

Request:

```json
{
  "message": "Tôi muốn mua 2 iPhone 15 dùng mã WINNER10 ship Hà Nội",
  "version": "v2",
  "session_id": "demo-session-01"
}
```

Response:

```json
{
  "version": "v2",
  "answer": "Tổng đơn hàng là 45,042,000 VND.",
  "latency_ms": 2103,
  "steps": 4,
  "tool_calls": [
    {
      "tool": "get_product_price",
      "args": {
        "product_name": "iPhone 15"
      },
      "result_preview": "24990000"
    },
    {
      "tool": "check_stock",
      "args": {
        "product_name": "iPhone 15",
        "quantity": 2
      },
      "result_preview": "available=12"
    }
  ],
  "trace_id": "trace_20260406_020",
  "status": "success",
  "error_code": null
}
```

Ghi chú:

- `version` có thể lấy từ request hoặc fallback sang `.env`
- `tool_calls` luôn có, nhưng `v1` trả mảng rỗng

## 2. Product APIs

### `GET /api/v1/products`

Danh sách sản phẩm đang active.

Query params:

- `q`: từ khóa tìm kiếm
- `category`: category

### `GET /api/v1/products/{product_id}`

Chi tiết sản phẩm.

### `GET /api/v1/products/search?q=iphone`

Search theo tên gần đúng.

Response mẫu:

```json
[
  {
    "id": 1,
    "sku": "IP15-128-BLK",
    "name": "iPhone 15",
    "price": 24990000,
    "weight_kg": 0.5,
    "stock": 12
  }
]
```

## 3. FAQ APIs

### `GET /api/v1/faqs`

Query params:

- `topic`
- `q`

Mục đích:

- `v1` chatbot có thể dùng như nguồn dữ liệu FAQ nội bộ
- frontend có thể hiển thị danh sách FAQ gợi ý

## 4. Tool APIs

Các endpoint này có thể được gọi nội bộ qua service layer, nhưng nên expose để:

- test độc lập
- debug dễ
- trình diễn tool behavior

### `POST /api/v1/tools/get-product-price`

Request:

```json
{
  "product_name": "iPhone 15"
}
```

Response:

```json
{
  "product_name": "iPhone 15",
  "unit_price": 24990000,
  "currency": "VND"
}
```

### `POST /api/v1/tools/check-stock`

Request:

```json
{
  "product_name": "iPhone 15",
  "quantity": 2
}
```

Response:

```json
{
  "product_name": "iPhone 15",
  "requested_quantity": 2,
  "available_quantity": 12,
  "in_stock": true
}
```

### `POST /api/v1/tools/get-coupon-discount`

Request:

```json
{
  "coupon_code": "WINNER10",
  "order_subtotal": 49980000
}
```

Response:

```json
{
  "coupon_code": "WINNER10",
  "is_valid": true,
  "discount_type": "percent",
  "discount_value": 10,
  "discount_amount": 3000000
}
```

### `POST /api/v1/tools/calc-shipping`

Request:

```json
{
  "destination_city": "Hà Nội",
  "total_weight_kg": 1.0
}
```

Response:

```json
{
  "destination_city": "Hà Nội",
  "shipping_fee": 40000,
  "estimated_days": 2
}
```

### `POST /api/v1/tools/build-quote`

Tùy chọn. Có thể để agent không dùng endpoint này trực tiếp nếu muốn giữ multi-step rõ ràng.

Request:

```json
{
  "items": [
    {
      "product_name": "iPhone 15",
      "quantity": 2
    }
  ],
  "coupon_code": "WINNER10",
  "destination_city": "Hà Nội"
}
```

Response:

```json
{
  "subtotal": 49980000,
  "discount_amount": 3000000,
  "shipping_fee": 40000,
  "total_amount": 47020000
}
```

## 5. Observability APIs

### `GET /api/v1/traces/{trace_id}`

Lấy trace đã lưu để hiển thị hoặc làm report.

### `GET /api/v1/metrics/summary`

Tổng hợp:

- total requests
- success rate
- average latency
- average steps theo version

## Error response chuẩn

```json
{
  "status": "error",
  "error_code": "COUPON_NOT_FOUND",
  "message": "Coupon SAVE999 does not exist",
  "trace_id": "trace_20260406_024"
}
```

## Mã lỗi đề xuất

- `PRODUCT_NOT_FOUND`
- `INSUFFICIENT_STOCK`
- `COUPON_NOT_FOUND`
- `COUPON_INVALID`
- `SHIPPING_RULE_NOT_FOUND`
- `TOOL_ARGUMENT_ERROR`
- `AGENT_PARSE_ERROR`
- `AGENT_MAX_STEPS_EXCEEDED`
- `LLM_PROVIDER_ERROR`

## Pydantic models gợi ý

- `ChatRequest`
- `ChatResponse`
- `ToolCallSummary`
- `ProductResponse`
- `FaqResponse`
- `PriceToolRequest`
- `StockToolRequest`
- `CouponToolRequest`
- `ShippingToolRequest`
