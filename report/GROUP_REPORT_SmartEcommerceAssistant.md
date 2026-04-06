# Group Report: Lab 3 - Smart E-commerce Assistant

- **Team Name**: E403-36
- **Project**: Smart E-commerce Assistant - Chatbot `v1` vs ReAct Agent `v2`
- **Team Members**:
  - Nguyễn Huy Tú (`2A202600170`)
  - Phạm Quốc Vương (`2A202600419`)
  - Trương Minh Phước (`2A202600330`)
  - Mai Văn Quân (`2A202600475`)
- **Submission Date**: 2026-04-06

---

## 1. Executive Summary

Nhóm xây dựng một MVP full-stack cho bài Lab 3 với mục tiêu so sánh công bằng giữa:

- `v1`: chatbot baseline, tối ưu cho FAQ và câu hỏi 1 bước
- `v2`: ReAct agent, phù hợp cho truy vấn nhiều bước cần gọi tool và grounding từ dữ liệu hệ thống

Hệ thống được triển khai trên cùng một nền tảng dùng chung:

- FastAPI backend
- Streamlit frontend
- PostgreSQL bằng Docker
- telemetry và trace JSON
- benchmark harness cho cùng bộ 5 test cases

Kết quả quan trọng nhất của dự án là:

- `v1` thắng ở các FAQ đơn giản nhờ độ trễ rất thấp
- `v2` thắng rõ ở các case quote nhiều bước, kiểm tra tồn kho, coupon và shipping
- hệ thống đã có guard `OUT_OF_DOMAIN`, fallback `fallback-seed`, metrics summary và trace chi tiết để phục vụ debugging và report

Theo `docs/compare_v1_v2_result.md`, ở lần runtime compare gần nhất:

| Version | Success Rate | Avg Latency (ms) | Avg Steps | Avg Total Tokens |
| :------ | :----------- | :--------------- | :-------- | :--------------- |
| `v1`    | `100%`       | `1.8`            | `1.6`     | `0.0`            |
| `v2`    | `100%`       | `9891.8`         | `3.8`     | `1920.6`         |

Điều này phản ánh đúng trade-off của bài lab: `v1` rẻ và nhanh hơn, còn `v2` chính xác hơn ở bài toán multi-step có tool grounding.

---

## 2. System Architecture and Tooling

### 2.1 Kiến trúc tổng thể

Hệ thống được thiết kế theo hướng cùng một backend phục vụ hai mode:

1. Người dùng nhập câu hỏi trên Streamlit UI
2. Frontend gọi `POST /api/v1/chat`
3. Backend route theo `version = v1 | v2 | compare`
4. `v1` xử lý bằng chatbot baseline
5. `v2` xử lý bằng ReAct agent với tool registry
6. Cả hai mode trả cùng một response schema để frontend render thống nhất
7. Telemetry, trace và metrics được ghi lại cho mọi request

### 2.2 Thành phần chính

- **Frontend**: `streamlit_app.py`
  - compare mode giữa `v1` và `v2`
  - hiển thị answer, latency, steps, tool calls, trace id
  - chạy benchmark 5 case trực tiếp từ UI
- **Backend**: `src/api/main.py` và các route trong `src/api/routes/`
  - `chat`, `products`, `tools`, `health`, `metrics`, `traces`
- **Data layer**:
  - `docker-compose.yml`
  - `db/init.sql`
  - `src/db/session.py`
  - `src/db/models.py`
- **Baseline Chatbot `v1`**:
  - `src/chatbot/chatbot.py`
  - ưu tiên FAQ, product lookup và chỉ fallback sang single-pass LLM khi cần
- **ReAct Agent `v2`**:
  - `src/agent/agent.py`
  - `src/agent/parser.py`
  - `src/agent/prompts.py`
  - `src/agent/tools_registry.py`
- **Observability and evaluation**:
  - `src/telemetry/logger.py`
  - `src/telemetry/trace_store.py`
  - `src/telemetry/metrics.py`
  - `src/api/routes/metrics.py`
  - `src/evaluation/benchmark_runner.py`
  - `docs/test_cases.md`

### 2.3 Tool inventory

`v2` sử dụng các tool grounded vào dữ liệu catalog và rules nội bộ:

- `get_faq_answer`
- `get_product_price`
- `check_stock`
- `get_coupon_discount`
- `calc_shipping`

Nhóm chọn cách tách tool rõ ràng thay vì gộp thành một endpoint tổng hợp để:

- dễ kiểm tra trace từng bước
- dễ benchmark số bước và tool calls
- làm rõ điểm khác biệt giữa chatbot và agent

### 2.4 Runtime and deployment support

Để phục vụ demo và build ổn định, nhóm có:

- `Dockerfile`
- `docker-compose.yml` cho `postgres`, `api`, `frontend`
- script chạy nhanh:
  - `scripts/run_postgres.ps1`
  - `scripts/run_backend.ps1`
  - `scripts/run_frontend.ps1`
  - `scripts/run_stack.ps1`
- chế độ `fallback-seed` khi Postgres chưa sẵn sàng

---

## 3. Team Contribution Breakdown

### Nguyễn Huy Tú (`2A202600170`)

Phụ trách phần nền tảng và tích hợp chung:

- sinh và hoàn thiện bộ tài liệu trong `docs/`
- dựng skeleton codebase ban đầu cho backend, frontend và cấu trúc thư mục
- xử lý fix bug, resolve conflict và đồng bộ các module khi nhóm ghép code
- viết và build cấu hình Docker:
  - `Dockerfile`
  - `docker-compose.yml`
  - các script chạy nhanh trong `scripts/`

### Phạm Quốc Vương (`2A202600419`)

Phụ trách **Phase 1-4** trong `docs/todo.md`:

- environment and bootstrapping
- PostgreSQL and data layer
- backend API and business logic
- chatbot `v1`

Deliverables chính:

- setup môi trường và hướng dẫn chạy
- schema PostgreSQL và seed data
- FastAPI routes cơ bản
- chatbot baseline trả response theo schema chung

### Trương Minh Phước (`2A202600330`)

Phụ trách **Phase 5** và hỗ trợ **Phase 6-9**:

- triển khai ReAct agent `v2`
- thiết kế loop `Thought -> Action -> Observation -> Final Answer`
- viết parser, prompt, tools registry
- hỗ trợ hoàn thiện UI compare, metrics, tests và provider integration

Deliverables chính:

- agent grounded bằng tools
- parser robust cho action format
- stopping conditions và fallback path
- hỗ trợ hardening toàn hệ thống sau benchmark

### Mai Văn Quân (`2A202600475`)

Phụ trách **Phase 6-9**:

- frontend Streamlit
- logging, metrics và evaluation
- test cases và validation
- provider abstraction và production-like validation

Deliverables chính:

- compare UI giữa `v1` và `v2`
- benchmark harness và bảng expected vs actual
- smoke tests, grounding tests, compare tests
- metrics summary và hỗ trợ nhiều provider

---

## 4. Evaluation and Validation

### 4.1 Bộ test dùng chung

Nhóm dùng cùng một bộ 5 test cases trong `docs/test_cases.md` để so sánh công bằng giữa `v1` và `v2`:

1. FAQ đổi trả
2. FAQ giao hàng cuối tuần
3. Tính tổng đơn hàng nhiều bước
4. Kiểm tra hàng và tính giá
5. Edge case coupon sai

Ngoài ra còn có case phụ cho `OUT_OF_DOMAIN` để kiểm tra guardrail mức hệ thống.

### 4.2 Kết quả tổng quan theo case

Theo `docs/compare_v1_v2_result.md`:

- Case 1 và 2: `v1` thắng vì trả lời đúng và nhanh hơn nhiều
- Case 3 và 4: `v2` thắng vì gọi đủ tool, tính đúng giá, tồn kho, coupon và shipping
- Case 5: `v2` thắng vì không hallucinate coupon, vẫn degrade gracefully và tính đúng tổng grounded

Một số kết quả cụ thể:

- iPhone 15 x2 + `WINNER10` + ship Hà Nội:
  - subtotal `49,980,000 VND`
  - discount `3,000,000 VND`
  - shipping `40,000 VND`
  - total `47,020,000 VND`
- MacBook Air M3 x1 + ship TP.HCM:
  - total `29,049,000 VND`
- AirPods Pro 2 x3 + `SAVE999` + ship Đà Nẵng:
  - coupon bị từ chối đúng
  - total `16,525,000 VND`

### 4.3 Telemetry and metrics

Nhóm đã triển khai đầy đủ observability để phục vụ report:

- JSON logger cho event-level log
- trace store cho từng request
- metrics summary theo `version` và `provider`
- live session metrics để nhìn nhanh hiệu năng

Các metric chính đã được track:

- `latency_ms`
- `steps`
- `tool_calls_count`
- `success_rate`
- `token_usage`
- `llm_calls`
- `provider`
- `model`
- `error_code`

### 4.4 Guardrails

Nhóm bổ sung guardrail ngoài phạm vi e-commerce:

- câu hỏi ngoài domain không đi vào `v1` hay `v2`
- không gọi provider
- không gọi tool
- trả `status = blocked`
- trả `error_code = OUT_OF_DOMAIN`

Điểm này quan trọng vì giúp tránh:

- tốn token không cần thiết
- trả lời lạc domain
- lộ lỗi kỹ thuật ra UI

---

## 5. Root Cause Analysis and Hardening

Trong quá trình hoàn thiện `v2`, nhóm gặp và xử lý nhiều failure mode điển hình của agent system:

### Case 1. Kết luận khi chưa đủ grounding

Vấn đề:

- model có thể phát `Final Answer` quá sớm
- FAQ hoặc quote chưa gọi đủ tool nhưng đã muốn kết luận

Khắc phục:

- suy ra `required_tools` từ user input
- chặn `Final Answer` nếu còn thiếu tool bắt buộc
- thêm step `insufficient_grounding`
- tự tổng hợp `auto_final_answer` khi đã đủ observation từ tools

### Case 2. Hallucination coupon hợp lệ

Vấn đề:

- với coupon sai như `SAVE999`, model có xu hướng bịa giảm giá

Khắc phục:

- buộc `v2` grounding kết quả coupon từ tool
- chỉ chấp nhận discount khi tool trả kết quả hợp lệ
- nếu tool báo lỗi, phản hồi đúng là coupon không hợp lệ hoặc không tồn tại

### Case 3. Parse quantity sai từ tên model sản phẩm

Vấn đề:

- các chuỗi như `MacBook Air M3` hoặc `AirPods Pro 2` dễ làm extractor hiểu nhầm số lượng

Khắc phục:

- bổ sung extractor test để tách quantity khỏi model number
- dùng test cases cụ thể cho `M3` và `Pro 2`

### Case 4. Repeated tool call và mixed output

Vấn đề:

- model có thể lặp lại tool đã gọi thành công
- có lúc output vừa chứa `Action` vừa chứa `Final Answer`

Khắc phục:

- thêm logic `Forced next missing tool`
- bỏ qua `Final Answer` nếu model vẫn còn emit `Action`
- log `parser_note` và `planner_note` để RCA dễ hơn

Các fix này được bảo vệ bằng test trong:

- `tests/test_api.py`
- `tests/test_api_compare.py`
- `tests/test_agent_grounding.py`
- `tests/test_domain_guard.py`

---

## 6. Production Readiness Review

### Điểm đã đạt được

- full-stack demo chạy được bằng Docker
- health check cho API và PostgreSQL
- fallback khi DB chưa sẵn sàng
- provider abstraction cho `mock`, `openai`, `gemini`, `local`
- compare UI phục vụ demo trực quan
- benchmark harness và telemetry phục vụ report
- test coverage cho luồng chính và edge cases quan trọng

---

## 7. Conclusion

Nhóm đã hoàn thành một hệ thống so sánh có tính kỹ thuật rõ ràng giữa chatbot baseline và ReAct agent trên cùng một use case thương mại điện tử. Điểm mạnh của bài làm không chỉ nằm ở việc có hai mode chạy được, mà còn ở chỗ cả hai đều được đặt trong cùng một khung đánh giá với trace, metrics, guardrail, benchmark harness và khả năng demo end-to-end.

Kết luận thực nghiệm của nhóm là:

- `v1` phù hợp cho câu hỏi đơn giản, nhanh và rẻ
- `v2` tạo giá trị thực khi bài toán cần nhiều bước và cần grounding
- để agent vận hành ổn định, phần engineering quanh parser, stopping condition, telemetry và tests quan trọng không kém chính model
