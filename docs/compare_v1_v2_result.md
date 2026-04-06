# Runtime Compare Report: v1 vs v2

Ngày chạy: `2026-04-06`

## Setup chạy thật

- Backend chạy thật qua HTTP tại `http://127.0.0.1:8000/api/v1/chat`
- Database runtime: SQLite file `F:\lab03-E403-36\runtime_eval.sqlite`
- Provider cho agent: `openai`
- Model: `gpt-4o-mini`
- API key được nạp từ `.env` khi restart backend
- Bộ case dùng để chạy: 5 case trong `docs/test_cases.md`
- Artifact của lần chạy cuối: `logs/benchmarks/benchmark_20260406_103108.json`
- Guard out-of-domain:
- câu hỏi ngoài phạm vi e-commerce không gọi LLM/tool
- API trả HTTP `200` với `status = blocked`, `error_code = OUT_OF_DOMAIN`
- câu trả lời cho người dùng nằm trong trường `answer`

## Tóm tắt nhanh

- `v1` vẫn là baseline nhanh và ổn định cho FAQ với độ trễ rất thấp.
- `v2` sau khi fix đã grounded đúng bằng tool cho cả FAQ và các case multi-step.
- Lỗi cũ đã được xử lý:
- không còn generic answer cho FAQ
- không còn hallucinate coupon hợp lệ
- không còn chốt `Final Answer` khi chưa đủ tool-grounded data
- không còn lấy nhầm số trong tên model làm quantity
- shipping được tính từ trọng lượng grounded theo catalog thay vì trọng lượng do model đoán

## Aggregate


| Version | Success Rate | Avg Latency (ms) | Avg Steps | Avg Total Tokens |
| ------- | ------------ | ---------------- | --------- | ---------------- |
| `v1`    | `100%`       | `1.8`            | `1.6`     | `0.0`            |
| `v2`    | `100%`       | `9891.8`         | `3.8`     | `1920.6`         |


## Kết quả theo case


| Case                             | Expected Winner | Actual Winner | v1                         | v2                             | Notes                                                          |
| -------------------------------- | --------------- | ------------- | -------------------------- | ------------------------------ | -------------------------------------------------------------- |
| `case_1` FAQ đổi trả             | `v1`            | `v1`          | success, `7 ms`, `1 step`  | success, `2385 ms`, `2 steps`  | Cả hai đều đúng; `v1` thắng theo latency                       |
| `case_2` FAQ giao hàng cuối tuần | `v1`            | `v1`          | success, `0 ms`, `1 step`  | success, `1727 ms`, `2 steps`  | Cả hai đều đúng; `v1` thắng theo latency                       |
| `case_3` Quote nhiều bước        | `v2`            | `v2`          | success, `0 ms`, `2 steps` | success, `19595 ms`, `6 steps` | `v2` gọi đủ tool và ra đúng tổng `47,020,000 VND`              |
| `case_4` Kiểm hàng và tính giá   | `v2`            | `v2`          | success, `1 ms`, `2 steps` | success, `9795 ms`, `4 steps`  | `v2` trả đúng stock, ship và tổng `29,049,000 VND`             |
| `case_5` Edge case coupon sai    | `v2`            | `v2`          | success, `1 ms`, `2 steps` | success, `15957 ms`, `5 steps` | `v2` xử lý đúng coupon sai, ship đúng và tổng `16,525,000 VND` |


## Chi tiết từng case

### Case 1

- Input: `Chính sách đổi trả là gì?`
- `v1` answer: đúng FAQ đổi trả.
- `v2` answer: đúng FAQ đổi trả qua tool `get_faq_answer`.
- Kết luận: hòa về độ đúng; winner runtime là `v1` vì nhanh hơn nhiều.
- Trace:
- `v1`: `trace_20260406_103019_035359`
- `v2`: `trace_20260406_103019_044108`

### Case 2

- Input: `Shop có giao hàng cuối tuần không?`
- `v1` answer: đúng FAQ giao hàng cuối tuần.
- `v2` answer: đúng FAQ giao hàng cuối tuần qua tool `get_faq_answer`.
- Kết luận: hòa về độ đúng; winner runtime là `v1` vì nhanh hơn rõ.
- Trace:
- `v1`: `trace_20260406_103021_430447`
- `v2`: `trace_20260406_103021_432069`

### Case 3

- Input: `Tôi muốn mua 2 iPhone 15, dùng mã WINNER10 và ship Hà Nội. Tổng bao nhiêu?`
- `v1` answer: chỉ trả catalog của iPhone 15.
- `v2` answer: đúng quote hoàn chỉnh.
- Tool calls của `v2`:
- `get_product_price`
- `get_coupon_discount`
- `calc_shipping`
- `check_stock`
- Kết quả đúng:
- subtotal: `49,980,000 VND`
- discount: `3,000,000 VND`
- shipping Hà Nội: `40,000 VND`
- total: `47,020,000 VND`
- Kết luận: `v2` thắng rõ.
- Trace:
- `v1`: `trace_20260406_103023_161468`
- `v2`: `trace_20260406_103023_163300`

### Case 4

- Input: `MacBook Air M3 còn hàng không? Nếu mua 1 cái ship TP.HCM thì hết bao nhiêu?`
- `v1` answer: chỉ trả catalog của MacBook Air M3.
- `v2` answer: đúng stock, đúng ship, đúng tổng.
- Tool calls của `v2`:
- `check_stock`
- `get_product_price`
- `calc_shipping`
- Kết quả đúng:
- giá máy: `28,990,000 VND`
- shipping TP.HCM: `59,000 VND`
- total: `29,049,000 VND`
- Kết luận: `v2` thắng rõ.
- Trace:
- `v1`: `trace_20260406_103042_762211`
- `v2`: `trace_20260406_103042_763850`

### Case 5

- Input: `Mua 3 AirPods Pro 2 dùng mã SAVE999 ship Đà Nẵng.`
- `v1` answer: chỉ trả catalog của AirPods Pro 2.
- `v2` answer: xử lý đúng coupon sai và vẫn tính được tổng grounded.
- Tool calls của `v2`:
- `check_stock`
- `get_product_price`
- `calc_shipping`
- Coupon `SAVE999` được phản ánh đúng là không hợp lệ hoặc không tồn tại.
- Kết quả đúng:
- subtotal: `16,470,000 VND`
- discount: `0 VND`
- shipping Đà Nẵng: `55,000 VND`
- total: `16,525,000 VND`
- Kết luận: `v2` thắng rõ.
- Trace:
- `v1`: `trace_20260406_103052_559023`
- `v2`: `trace_20260406_103052_561031`

## Nhận xét kỹ thuật

- `v1` phù hợp cho FAQ và product lookup cơ bản.
- `v2` hiện đã đúng với mục tiêu agent hơn:
- có reasoning log rõ
- dùng tool để grounding
- chỉ kết luận khi đủ dữ liệu
- graceful degradation đúng cho coupon invalid
- Out-of-domain hiện được chặn ở tầng `chat_service` trước khi vào `v1` hoặc `v2`.
- Khi gặp out-of-domain, hệ thống không trả lỗi kỹ thuật ra UI mà trả một phản hồi thân thiện cho người dùng với:
- `status = blocked`
- `error_code = OUT_OF_DOMAIN`
- `answer =` câu thông báo chỉ hỗ trợ câu hỏi về cửa hàng điện tử
- Điểm đánh đổi là chi phí và latency cao hơn đáng kể so với `v1`.

## Kiểm tra Out-of-Domain

- Input runtime check: `Thời tiết hôm nay thế nào?`
- Endpoint: `POST http://127.0.0.1:8000/api/v1/chat`
- Runtime DB: `runtime_eval.sqlite`
- Kết quả mong đợi:
- không có `tool_calls`
- không có `reasoning_steps`
- không gọi provider
- trả ngay:

```json
{
  "status": "blocked",
  "error_code": "OUT_OF_DOMAIN",
  "answer": "Tôi chỉ hỗ trợ câu hỏi liên quan đến cửa hàng điện tử trong bài lab này, ví dụ sản phẩm, giá, tồn kho, mã giảm giá, giao hàng, đổi trả hoặc bảo hành."
}
```

- Kết quả kiểm tra thực tế sau restart backend: khớp mong đợi.

## Artifacts

- Raw JSON kết quả run cuối: `logs/benchmarks/benchmark_20260406_102913.json`
- SQLite runtime DB: `runtime_eval.sqlite`
- Backend log:
- `logs/backend_eval.out.log`
- `logs/backend_eval.err.log`

