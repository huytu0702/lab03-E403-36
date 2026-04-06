# Individual Report: Lab 3 - Mai Văn Quân

- **Student Name**: Mai Văn Quân
- **Student ID**: 2A202600475
- **Date**: 2026-04-06

---

## I. Technical Contribution

### Scope of Work

Tôi phụ trách **Phase 6, 7, 8, 9**:

- frontend Streamlit
- logging, metrics và evaluation
- test cases và validation
- providers và production-like validation

### Main Modules

- `streamlit_app.py`
- `src/api/routes/metrics.py`
- `src/telemetry/logger.py`
- `src/telemetry/trace_store.py`
- `src/telemetry/metrics.py`
- `src/evaluation/benchmark_runner.py`
- `src/evaluation/benchmark_cases.py`
- `scripts/run_benchmark.py`
- `tests/test_api.py`
- `tests/test_api_compare.py`
- `tests/test_domain_guard.py`
- `src/core/provider_factory.py`
- `src/core/mock_provider.py`
- `src/core/openai_provider.py`
- `src/core/gemini_provider.py`
- `src/core/local_provider.py`

### Contribution Details

Tôi tập trung vào phần giúp hệ thống có thể demo, đo lường và xác minh được:

- xây compare UI giữa `v1` và `v2` trên cùng một câu hỏi
- hiển thị answer, latency, steps, tool calls, trace id và reasoning steps
- xây metrics summary endpoint để tổng hợp theo version và provider
- định nghĩa 5 test cases dùng chung và benchmark harness
- bổ sung smoke tests, compare tests và out-of-domain guard tests
- hỗ trợ provider abstraction để hệ thống chạy được với `mock`, `openai`, `gemini`, `local`

---

## II. Debugging Case Study

### Problem

Một vấn đề lớn ở giai đoạn cuối là “hệ thống có chạy” chưa đủ để kết luận bài làm tốt. Nếu không có metrics và evaluation rõ ràng thì:

- rất khó chứng minh `v2` hơn `v1` ở đâu
- không biết latency, steps, token usage tăng bao nhiêu
- không biết UI có đang hiển thị đúng đường đi thật của backend hay không

### Diagnosis

Tôi xem phần evaluation như một lớp sản phẩm riêng, không chỉ là phụ kiện:

- frontend phải đọc cùng response schema cho cả `v1` và `v2`
- benchmark phải dùng cùng 5 case để so sánh công bằng
- metrics phải tổng hợp được theo `version` và `provider`
- out-of-domain phải được chặn sớm để không làm bẩn số liệu

### Solution

Tôi tập trung hoàn thiện:

- compare mode trong `streamlit_app.py`
- benchmark harness trong `src/evaluation/benchmark_runner.py`
- metrics endpoint trong `src/api/routes/metrics.py`
- test cho compare response, metrics breakdown và out-of-domain guard

Ngoài ra, phần provider abstraction giúp nhóm:

- benchmark local với `mock`
- chuyển qua provider thật khi có API key
- có fallback hợp lý cho môi trường demo

### Result

Nhờ đó, nhóm có thể:

- demo trực tiếp sự khác biệt giữa `v1` và `v2`
- đọc metrics summary ngay trong UI
- chạy benchmark 5 case có expected vs actual
- viết report dựa trên trace và evaluation thay vì cảm tính

---

## III. Personal Insights

Tôi rút ra rằng observability và validation là phần bắt buộc nếu muốn gọi một hệ thống là “agentic” theo hướng kỹ thuật nghiêm túc. Không có trace, benchmark và metrics thì rất dễ nhầm giữa “agent đang reasoning tốt” và “agent chỉ trả ra một câu nghe hợp lý”.

Tôi cũng thấy việc hỗ trợ nhiều provider giúp bài lab thực tế hơn. `mock` rất hữu ích cho local dev và test nhanh, còn provider thật mới cho thấy chi phí thực của `v2`: chậm hơn và tốn token hơn nhiều. Chính vì vậy, compare UI và metrics summary là phần không thể thiếu để giải thích trade-off cho người xem demo.

---

## IV. Future Improvements

- thêm dashboard trực quan hơn cho metrics theo thời gian
- tăng test coverage cho provider failure và fallback path
- tự động hóa bước chụp screenshot/report artifact sau mỗi lần benchmark
