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

- nâng cấp [streamlit_app.py](F:/lab03-E403-36/streamlit_app.py) thành compare mode giữa `v1` và `v2`
- thêm prompt mẫu cho 5 test cases trong sidebar
- thêm chat history để demo liên tục trước lớp
- thêm health check và metrics summary ngay trong UI
- hiển thị answer, latency, steps, trace id và tool calls rõ ràng hơn

### Còn làm

- chụp screenshot đẹp cho report
- polish thêm màu sắc hoặc layout nếu muốn

## Phase 7. Logging, Metrics, and Evaluation

### Đã xong

- có logger JSON trong [src/telemetry/logger.py](F:/lab03-E403-36/src/telemetry/logger.py)
- có trace store trong [src/telemetry/trace_store.py](F:/lab03-E403-36/src/telemetry/trace_store.py)
- có metrics summary endpoint ở [src/api/routes/metrics.py](F:/lab03-E403-36/src/api/routes/metrics.py)
- tổng hợp được `success_rate`, `avg_latency_ms`, `avg_steps`, `avg_tool_calls`, token usage theo version
- có benchmark harness ở [scripts/run_benchmark.py](F:/lab03-E403-36/scripts/run_benchmark.py)

### Còn làm

- đưa screenshot hoặc bảng benchmark cuối cùng vào report nhóm

## Phase 8. Test Cases and Validation

### Đã xong

- đã định nghĩa 5 test cases trong [docs/test_cases.md](F:/lab03-E403-36/docs/test_cases.md)
- thêm `pytest` smoke tests ở [tests/test_api.py](F:/lab03-E403-36/tests/test_api.py)
- đã cover API health, products, tools, coupon lỗi và chat `v1`/`v2`
- có test harness chạy cùng một bộ case cho `v1` và `v2`
- benchmark lưu expected vs actual vào `logs/benchmarks/benchmark_latest.json`

### Còn làm

- trước lúc nộp bài, chạy benchmark lại 1 lần trên máy demo chính thức để chụp kết quả mới nhất

## Phase 9. Providers and Production-like Validation

### Đã xong

- có provider abstraction sẵn trong `src/core`
- nâng cấp `mock` provider để local dev benchmark được ngay cả khi chưa có API key
- thêm usage tracking theo provider/model và graceful error handling cho local GGUF provider
- app vẫn chạy được ở chế độ `fallback-seed` nếu Docker/Postgres chưa sẵn sàng

### Còn làm

- nếu nhóm có API key thật, set `DEFAULT_PROVIDER=openai` hoặc `gemini` trong `.env` rồi chạy benchmark lại để lấy số liệu production-like cuối cùng
- nếu muốn chạy local GGUF, cài thêm `pip install -r requirements-local.txt`

## Ưu tiên thực hiện tiếp theo

1. Nối backend và services sang PostgreSQL thật
2. Viết test cho `v1`, `v2`, tools và edge cases
3. Nâng `v2` thành ReAct loop thật dùng LLM
4. Hoàn thiện compare UI và metrics summary
