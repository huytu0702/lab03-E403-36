# Test Cases

## Mục tiêu

Dùng cùng 5 test cases cho `v1` và `v2` để so sánh công bằng.

Phân bố đúng rubric:

- 2 case chatbot thắng
- 2 case agent thắng
- 1 edge case

## Cách đánh giá

Mỗi case ghi:

- expected behavior
- actual output `v1`
- actual output `v2`
- ai thắng
- lý do

## Case 1. FAQ đổi trả

### Input

```text
Chính sách đổi trả là gì?
```

### Kỳ vọng

- trả lời đúng theo `faqs`
- không bịa thêm chính sách

### Dự đoán

- `v1` thắng hoặc hòa

### Lý do

- 1 bước
- không cần tool
- chatbot thường nhanh hơn và rẻ hơn

## Case 2. FAQ giao hàng cuối tuần

### Input

```text
Shop có giao hàng cuối tuần không?
```

### Kỳ vọng

- trả lời đúng theo FAQ

### Dự đoán

- `v1` thắng hoặc hòa

### Lý do

- không cần multi-step reasoning

## Case 3. Tính tổng đơn hàng nhiều bước

### Input

```text
Tôi muốn mua 2 iPhone 15, dùng mã WINNER10 và ship Hà Nội. Tổng bao nhiêu?
```

### Kỳ vọng

- lấy đúng giá iPhone 15
- kiểm tra tồn kho cho số lượng 2
- áp coupon đúng rule
- tính shipping theo Hà Nội
- trả tổng tiền cuối cùng

### Dự đoán

- `v2` thắng

### Lý do

- phụ thuộc nhiều bước
- cần grounding từ DB

## Case 4. Kiểm tra hàng và tính giá

### Input

```text
MacBook Air M3 còn hàng không? Nếu mua 1 cái ship TP.HCM thì hết bao nhiêu?
```

### Kỳ vọng

- trả đúng stock
- tính đúng tổng giá + ship

### Dự đoán

- `v2` thắng

### Lý do

- cần stock + price + shipping

## Case 5. Edge case coupon sai

### Input

```text
Mua 3 AirPods Pro 2 dùng mã SAVE999 ship Đà Nẵng.
```

### Kỳ vọng

- phát hiện coupon không tồn tại hoặc không hợp lệ
- vẫn có thể trả subtotal và shipping nếu muốn
- không bịa ra discount

### Dự đoán

- `v2` thường xử lý an toàn hơn
- nhưng đây là edge case để chấm graceful degradation

## Bảng kết quả đề xuất

| Case | Type | Expected | v1 | v2 | Winner | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | chatbot-win | FAQ đúng |  |  |  |  |
| 2 | chatbot-win | FAQ đúng |  |  |  |  |
| 3 | agent-win | quote đúng |  |  |  |  |
| 4 | agent-win | stock + total đúng |  |  |  |  |
| 5 | edge | graceful error |  |  |  |  |

## Metrics ghi cho từng case

- `latency_ms`
- `steps`
- `tool_calls_count`
- `success`
- `error_code`
- `final_answer_correctness`

## Gợi ý chấm thắng thua

`v1` thắng khi:

- trả lời đủ đúng
- nhanh hơn
- ít token hơn

`v2` thắng khi:

- đúng dữ liệu hơn
- xử lý multi-step tốt hơn
- trace giải thích được đường đi
