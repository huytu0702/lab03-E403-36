# Remaining Work by Phase

## Mục tiêu

Tài liệu này liệt kê các phần **chưa làm** hoặc mới ở mức skeleton, được nhóm lại theo từng phase triển khai để dễ giao việc và theo dõi tiến độ.

## Phase 1. Environment and Bootstrapping

### Đã xong

- tạo `.venv`
- cài dependencies nền
- tạo `.env` từ `.env.example`
- dựng skeleton FastAPI và Streamlit

### Còn làm

- chuẩn hóa hướng dẫn setup cho toàn team trong `README`
- xác nhận mọi máy trong nhóm chạy cùng version Python
- thêm script chạy nhanh cho backend và frontend nếu cần

## Phase 2. PostgreSQL and Data Layer

### Đã xong

- tạo [docker-compose.yml](F:/lab03-E403-36/docker-compose.yml)
- tạo [db/init.sql](F:/lab03-E403-36/db/init.sql)
- tạo skeleton DB package:
  - [src/db/session.py](F:/lab03-E403-36/src/db/session.py)
  - [src/db/models.py](F:/lab03-E403-36/src/db/models.py)

### Còn làm

- chạy và verify Postgres bằng Docker thật
- hoàn thiện schema đầy đủ cho:
  - `products`
  - `inventory`
  - `coupons`
  - `shipping_rules`
  - `faqs`
  - `quote_logs` nếu dùng
- seed dữ liệu thật vào Postgres
- viết repository hoặc query layer thay cho seed in-memory
- nối service layer sang DB thật

## Phase 3. Backend API and Business Logic

### Đã xong

- tạo entrypoint FastAPI: [src/api/main.py](F:/lab03-E403-36/src/api/main.py)
- tạo route cơ bản:
  - [src/api/routes/chat.py](F:/lab03-E403-36/src/api/routes/chat.py)
  - [src/api/routes/products.py](F:/lab03-E403-36/src/api/routes/products.py)
  - [src/api/routes/tools.py](F:/lab03-E403-36/src/api/routes/tools.py)
  - [src/api/routes/traces.py](F:/lab03-E403-36/src/api/routes/traces.py)

### Còn làm

- chuyển tất cả API từ seed in-memory sang DB thật
- hoàn thiện response/error contract nhất quán cho mọi endpoint
- thêm endpoint metrics summary
- thêm validate input chặt hơn cho tools
- thêm error mapping rõ cho:
  - `PRODUCT_NOT_FOUND`
  - `INSUFFICIENT_STOCK`
  - `COUPON_NOT_FOUND`
  - `COUPON_INVALID`
  - `SHIPPING_RULE_NOT_FOUND`

## Phase 4. Chatbot `v1`

### Đã xong

- tạo baseline chatbot ở [src/chatbot/chatbot.py](F:/lab03-E403-36/src/chatbot/chatbot.py)
- có trace cơ bản cho chatbot
- trả response theo schema chung

### Còn làm

- thiết kế prompt `v1` rõ ràng hơn
- bổ sung context retrieval cho FAQ và product info
- tối ưu fallback khi câu hỏi mơ hồ
- đảm bảo `v1` vẫn đơn giản, không vô tình thành agent
- đo metrics thật khi dùng provider ngoài `mock`

## Phase 5. ReAct Agent `v2`

### Đã xong

- có skeleton agent chạy được ở [src/agent/agent.py](F:/lab03-E403-36/src/agent/agent.py)
- có tools registry:
  - [src/agent/tools_registry.py](F:/lab03-E403-36/src/agent/tools_registry.py)
- có parser cơ bản:
  - [src/agent/parser.py](F:/lab03-E403-36/src/agent/parser.py)
- có trace từng bước

### Còn làm

- thay deterministic plan bằng ReAct loop thật dùng LLM
- parse `Thought`, `Action`, `Observation`, `Final Answer` từ model output
- thêm robust parser cho JSON hoặc action format
- thêm retry/fallback khi parse lỗi
- thêm stopping condition tốt hơn ngoài `max_steps`
- đảm bảo agent chỉ dùng dữ liệu có grounding từ tools

## Phase 6. Frontend Streamlit

### Đã xong

- có UI cơ bản ở [streamlit_app.py](F:/lab03-E403-36/streamlit_app.py)
- chọn được `v1` hoặc `v2`
- hiển thị answer, latency, steps, trace id và tool calls

### Còn làm

- thêm compare view giữa `v1` và `v2` trên cùng input
- thêm chat history
- thêm bảng benchmark 5 test cases
- hiển thị trace theo dạng dễ đọc hơn
- cải thiện UX để demo trước lớp

## Phase 7. Logging, Metrics, and Evaluation

### Đã xong

- có logger JSON trong [src/telemetry/logger.py](F:/lab03-E403-36/src/telemetry/logger.py)
- có trace store trong [src/telemetry/trace_store.py](F:/lab03-E403-36/src/telemetry/trace_store.py)
- có log step cơ bản cho `v1` và `v2`

### Còn làm

- thêm summary metrics endpoint
- tính success rate, average latency, average steps theo version
- ghi token usage và provider metrics thật
- chuẩn hóa trace file cho report
- tạo script tổng hợp kết quả benchmark từ logs/traces

## Phase 8. Test Cases and Validation

### Đã xong

- đã định nghĩa 5 test cases trong [docs/test_cases.md](F:/lab03-E403-36/docs/test_cases.md)
- đã verify thủ công `v1`, `v2`, và `/traces/{trace_id}`

### Còn làm

- viết `pytest` cho API mới
- viết test cho tools endpoints
- viết test cho edge cases:
  - coupon sai
  - không đủ hàng
  - city không có rule ship
  - product không tồn tại
- tạo test harness chạy cùng một bộ case cho `v1` và `v2`
- lưu expected vs actual để đưa vào report

## Phase 9. Providers and Production-like Validation

### Đã xong

- có provider abstraction sẵn trong `src/core`
- có `mock` provider để local dev không cần API key

### Còn làm

- test thật với OpenAI hoặc Gemini
- đo latency và token usage thật
- xử lý lỗi provider timeout hoặc API failure
- cân nhắc cài `requirements-local.txt` nếu muốn test local GGUF model

## Ưu tiên thực hiện tiếp theo

1. Nối backend và services sang PostgreSQL thật
2. Viết test cho `v1`, `v2`, tools và edge cases
3. Nâng `v2` thành ReAct loop thật dùng LLM
4. Hoàn thiện compare UI và metrics summary
