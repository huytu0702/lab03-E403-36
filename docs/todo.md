# Remaining Work

## Mục tiêu

Tài liệu này tóm tắt ngắn gọn các phần **chưa làm** hoặc mới ở mức skeleton trong MVP hiện tại.

## Chưa hoàn thành

### 1. Database thật chưa nối vào app

- `v1` và `v2` vẫn đang đọc dữ liệu từ seed in-memory
- chưa query Postgres qua repository hoặc service layer
- chưa verify end-to-end giữa FastAPI và PostgreSQL

### 2. CRUD và repository chưa hoàn chỉnh

- chưa có repository thật cho:
  - `products`
  - `inventory`
  - `coupons`
  - `shipping_rules`
  - `faqs`
- model DB mới ở mức skeleton

### 3. ReAct agent chưa là bản LLM-driven hoàn chỉnh

- `v2` hiện chạy theo deterministic plan
- chưa parse `Thought`, `Action`, `Final Answer` từ output model
- chưa có retry hoặc guardrail khi parse lỗi

### 4. Chatbot `v1` mới là baseline tối thiểu

- chưa có prompt/context pipeline hoàn chỉnh
- chưa tối ưu cho FAQ, product context và fallback behavior

### 5. Frontend Streamlit còn rất cơ bản

- chưa có compare view `v1` vs `v2`
- chưa có lịch sử chat
- chưa có bảng benchmark 5 test cases
- chưa render trace theo dạng dễ demo

### 6. Test và evaluation chưa làm

- chưa có test suite `pytest` cho API mới
- chưa có test cho edge cases
- chưa có script benchmark 5 test cases
- chưa có bảng expected vs actual tự động

### 7. Metrics và observability chưa đủ

- chưa có endpoint summary metrics
- chưa có dashboard tổng hợp latency, steps, success rate
- mới có trace file và log event cơ bản

### 8. Provider thật chưa được kiểm thử

- hệ thống đang mặc định dùng `mock`
- chưa test thực tế với OpenAI hoặc Gemini
- chưa đo latency và token usage thật

## Ưu tiên tiếp theo

1. Nối backend với PostgreSQL thật
2. Viết test cho `v1`, `v2`, tools và edge cases
3. Nâng `v2` thành ReAct loop thật dùng LLM
4. Hoàn thiện UI compare và benchmark
