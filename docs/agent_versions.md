# Agent v1 và v2

Tài liệu này mô tả cách hoạt động thực tế của hai phiên bản trong codebase hiện tại:

- `v1`: chatbot baseline
- `v2`: ReAct agent có tool calling

## 1. Agent `v1` hoạt động như thế nào

`v1` được implement trong `src/chatbot/chatbot.py` dưới class `BaselineChatbot`.

Luồng xử lý:

1. Tạo trace với `version="v1"`.
2. Thử match câu hỏi với FAQ nội bộ trước.
3. Nếu không match FAQ, thử detect sản phẩm trong câu hỏi để trả thông tin catalog cơ bản.
4. Nếu vẫn không có grounding từ FAQ hoặc catalog, fallback sang 1 lần gọi LLM duy nhất.
5. Trả về answer, reasoning steps, trace id và metrics.

Đặc điểm chính của `v1`:

- Không có ReAct loop.
- Không có multi-step orchestration.
- Không gọi tool qua `tools_registry`.
- `tool_calls` luôn là mảng rỗng.
- Tối ưu cho câu hỏi đơn giản như FAQ hoặc tra cứu sản phẩm cơ bản.

Khi nào `v1` mạnh:

- Câu hỏi FAQ nội bộ.
- Câu hỏi chỉ cần giá/tồn kho mô tả cơ bản của một sản phẩm.
- Trường hợp cần phản hồi nhanh, chi phí thấp.

Hạn chế của `v1`:

- Không tự phối hợp nhiều bước như kiểm tồn kho + coupon + ship + tổng tiền.
- Khi fallback sang LLM, câu trả lời không grounded bằng tool result như `v2`.

## 2. Agent `v2` hoạt động như thế nào

`v2` được implement trong `src/agent/agent.py` dưới class `ReActAgent`.

`v2` dùng mô hình ReAct:

- `Thought`
- `Action`
- `Action Input`
- backend chạy tool
- `Observation`
- lặp lại cho đến khi đủ dữ liệu
- `Final Answer`

Luồng xử lý chính:

1. Tạo trace với `version="v2"`.
2. Build system prompt từ danh sách tool trong `src/agent/tools_registry.py`.
3. Phân tích câu hỏi để suy ra các tool bắt buộc bằng `_infer_required_tools(...)`.
4. Gọi LLM theo từng bước để model sinh ra:
   - `Action` + `Action Input`, hoặc
   - `Final Answer`
5. Nếu model yêu cầu tool:
   - backend validate/chuẩn hóa args bằng `_prepare_tool_args(...)`
   - thực thi tool thật bằng `_execute_tool(...)`
   - ghi `Observation` vào scratchpad
6. Nếu đã đủ toàn bộ required tools, backend tự tổng hợp grounded answer bằng `_build_grounded_answer(...)`.
7. Nếu model kết luận quá sớm khi còn thiếu tool, backend chặn lại và buộc tiếp tục loop.
8. Kết thúc khi:
   - có đủ dữ liệu grounded và trả lời thành công, hoặc
   - lỗi provider, parse lỗi lặp lại quá giới hạn, hoặc
   - chạm `max_steps`

Đặc điểm chính của `v2`:

- Có ReAct loop nhiều bước.
- Có tool registry riêng.
- Có cơ chế chống kết luận sớm khi thiếu grounding.
- Có cơ chế ép gọi tool còn thiếu nếu model lặp lại tool cũ.
- `tool_calls` chứa lịch sử các tool đã chạy thành công.

## 3. Cơ chế grounding của `v2`

`v2` không được phép kết luận nếu chưa đủ dữ liệu từ tool.

Hai lớp bảo vệ chính:

### 3.1. Suy ra tool bắt buộc trước khi loop

Hàm `_infer_required_tools(...)` xác định tool nào bắt buộc dựa trên nội dung user query:

- Nếu là FAQ: bắt buộc `get_faq_answer`
- Nếu hỏi giá: thêm `get_product_price`
- Nếu hỏi còn hàng hoặc mua nhiều sản phẩm: thêm `check_stock`
- Nếu có mã giảm giá: thêm `get_coupon_discount`
- Nếu có thành phố giao hàng: thêm `calc_shipping`

### 3.2. Không cho `Final Answer` khi còn thiếu tool

Nếu model trả `Final Answer` nhưng `required_tools` chưa được gọi đủ, agent sẽ:

- ghi step với trạng thái `insufficient_grounding`
- thêm observation yêu cầu gọi các tool còn thiếu
- tiếp tục loop thay vì trả lời ngay

Ngoài ra, nếu model lặp lại một tool đã gọi thành công trong khi vẫn còn tool thiếu, agent sẽ dùng `_next_missing_tool_call(...)` để ép chuyển sang tool còn thiếu tiếp theo.

## 4. Danh sách tool hiện có của `v2`

Tất cả tool của agent hiện được khai báo trong `src/agent/tools_registry.py`.

### 4.1. `get_faq_answer`

Mục đích:

- Lấy câu trả lời FAQ grounded từ knowledge base nội bộ.

Args:

- `user_message`

Kết quả điển hình:

```json
{
  "topic": "return_policy",
  "question": "...",
  "answer": "..."
}
```

Khi dùng:

- Câu hỏi chính sách đổi trả, bảo hành, giao hàng cuối tuần, FAQ nội bộ.

### 4.2. `get_product_price`

Mục đích:

- Lấy đơn giá của sản phẩm.

Args:

- `product_name`

Kết quả điển hình:

```json
{
  "product_name": "iPhone 15",
  "unit_price": 22990000,
  "currency": "VND"
}
```

Khi dùng:

- Hỏi giá sản phẩm.
- Cần subtotal để tính tổng đơn hàng.

### 4.3. `check_stock`

Mục đích:

- Kiểm tra số lượng yêu cầu có đủ hàng không.

Args:

- `product_name`
- `quantity`

Kết quả điển hình:

```json
{
  "product_name": "iPhone 15",
  "requested_quantity": 2,
  "available_quantity": 8,
  "in_stock": true
}
```

Khi dùng:

- User hỏi "còn hàng không".
- User yêu cầu mua nhiều hơn 1 sản phẩm.

### 4.4. `get_coupon_discount`

Mục đích:

- Validate mã giảm giá và tính số tiền được giảm.

Args:

- `coupon_code`
- `order_subtotal`

Kết quả điển hình:

```json
{
  "coupon_code": "WINNER10",
  "is_valid": true,
  "discount_type": "percent",
  "discount_value": 10.0,
  "discount_amount": 2299000
}
```

Khi dùng:

- User cung cấp coupon.
- Cần tính tổng thanh toán sau giảm giá.

### 4.5. `calc_shipping`

Mục đích:

- Tính phí ship theo thành phố và tổng khối lượng đơn hàng.

Args:

- `destination_city`
- `total_weight_kg`

Kết quả điển hình:

```json
{
  "destination_city": "TP.HCM",
  "shipping_fee": 30000,
  "estimated_days": 2
}
```

Khi dùng:

- User hỏi phí ship hoặc tổng tiền có bao gồm giao hàng.

## 5. Cách agent chuẩn hóa tham số tool

Trong `v2`, một số tham số không phụ thuộc hoàn toàn vào output của model.

Hàm `_prepare_tool_args(...)` tự bổ sung:

- `order_subtotal` cho `get_coupon_discount`
- `total_weight_kg` cho `calc_shipping`

Nguồn dữ liệu để chuẩn hóa:

- tên sản phẩm trích từ câu hỏi
- số lượng trích từ câu hỏi
- trọng lượng sản phẩm trong catalog
- đơn giá sản phẩm trong catalog

Điểm này giúp giảm lỗi khi model quên tính subtotal hoặc weight trước khi gọi tool.

## 6. Tool API endpoints ở backend

Ngoài tool registry cho agent, backend cũng expose các endpoint để test tool trực tiếp tại `src/api/routes/tools.py`:

- `POST /api/v1/tools/get-product-price`
- `POST /api/v1/tools/check-stock`
- `POST /api/v1/tools/get-coupon-discount`
- `POST /api/v1/tools/calc-shipping`

Lưu ý:

- `get_faq_answer` hiện có trong agent registry nhưng chưa được expose thành endpoint trong `tools.py`.
- Vì vậy tool FAQ đang là tool nội bộ của agent, không phải public tool API giống 4 tool còn lại.

## 7. So sánh nhanh `v1` và `v2`

| Tiêu chí | `v1` | `v2` |
|---|---|---|
| Kiểu hệ thống | Chatbot baseline | ReAct agent |
| Số bước suy luận | Chủ yếu 1 pass | Nhiều bước |
| Tool calling | Không | Có |
| Grounding | FAQ/catalog trước, sau đó có thể fallback LLM | Bắt buộc grounded bằng tool cho các case phù hợp |
| Multi-step query | Yếu | Mạnh |
| Latency | Thấp | Cao hơn |
| `tool_calls` | Luôn rỗng | Có dữ liệu thực thi tool |
| Use case phù hợp | FAQ, lookup cơ bản | Quote nhiều bước, stock + coupon + shipping |

## 8. Kết luận

- `v1` phù hợp làm baseline nhanh, đơn giản, rẻ, dễ so sánh.
- `v2` đúng vai trò agent hơn vì có loop, có tool registry, có grounding và có cơ chế chống kết luận thiếu dữ liệu.
- Trong implementation hiện tại, điểm khác biệt quan trọng nhất không nằm ở model mà nằm ở orchestration và cách dùng tool.
