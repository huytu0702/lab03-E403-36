# Individual Report: Lab 3 - Phạm Quốc Vương

- **Student Name**: Phạm Quốc Vương
- **Student ID**: 2A202600419
- **Date**: 2026-04-06

---

## I. Technical Contribution

### Scope of Work

Tôi phụ trách **Phase 1, 2, 3, 4** theo `docs/todo.md`:

- environment and bootstrapping
- PostgreSQL and data layer
- backend API and business logic
- chatbot baseline `v1`

### Main Modules

- `.env.example`
- `README.md`
- `db/init.sql`
- `src/db/session.py`
- `src/db/models.py`
- `src/api/main.py`
- `src/api/routes/chat.py`
- `src/api/routes/products.py`
- `src/api/routes/tools.py`
- `src/api/routes/health.py`
- `src/services/product_service.py`
- `src/services/faq_service.py`
- `src/services/chat_service.py`
- `src/chatbot/chatbot.py`

### Contribution Details

Ở Phase 1-4, tôi tập trung hoàn thiện nền chạy và baseline business flow:

- chuẩn hóa môi trường để nhóm dùng chung Python version và `.env`
- xây dựng schema PostgreSQL cho `products`, `inventory`, `coupons`, `shipping_rules`, `faqs`
- seed dữ liệu cố định để mọi test case dùng cùng nguồn sự thật
- dựng các route FastAPI cơ bản cho chat, products, tools và health
- viết chatbot `v1` theo hướng đơn giản, ưu tiên FAQ và product lookup trước khi fallback sang LLM

### Technical Highlights

`v1` được giữ đúng vai trò baseline:

- trả lời nhanh cho FAQ
- có thể trả product info cơ bản
- không orchestration multi-step như agent
- vẫn ghi trace theo schema chung để frontend compare công bằng

Thiết kế này quan trọng vì nếu `v1` bị làm quá mạnh, việc so sánh với `v2` sẽ mất ý nghĩa.

---

## II. Debugging Case Study

### Problem

Một vấn đề điển hình ở Phase 2-4 là dữ liệu và flow dễ bị lệch giữa:

- database thật
- seed data fallback
- câu trả lời do chatbot sinh ra

Nếu không kiểm soát chặt, chatbot có thể:

- trả thông tin sản phẩm không đúng catalog
- bỏ qua FAQ có sẵn
- sinh câu trả lời không nhất quán với dữ liệu hệ thống

### Diagnosis

Tôi xác định baseline cần một luồng ưu tiên rõ ràng:

1. FAQ lookup
2. Product lookup
3. Chỉ khi không có grounding mới fallback sang LLM

Nếu đảo thứ tự hoặc phụ thuộc LLM quá sớm, `v1` vừa tốn token vừa khó kiểm soát factuality.

### Solution

Tôi định hình lại luồng `v1` trong `src/chatbot/chatbot.py` theo 3 tầng:

- match FAQ trước
- nếu không có FAQ thì detect product trong câu hỏi
- nếu vẫn không có grounding thì mới single-pass LLM

Đồng thời phần data layer được tách rõ bằng:

- schema SQL có seed cố định
- session DB chung
- service layer dùng lại cho API và chatbot

### Result

Sau khi ổn định luồng này:

- `v1` xử lý tốt 2 FAQ case
- trả product info ổn định cho các câu hỏi đơn giản
- có trace rõ ràng với `faq_hit`, `faq_miss`, `product_hit`, `product_miss`
- tạo được baseline sạch để so sánh với agent

---

## III. Personal Insights

Qua phần việc của mình, tôi thấy chatbot baseline vẫn rất hữu ích nếu phạm vi được định nghĩa đúng. Với FAQ và product lookup, `v1` nhanh, rẻ và dễ kiểm soát hơn `v2`. Đây là điểm quan trọng trong thực tế: không phải lúc nào cũng cần agent.

Tuy nhiên, giới hạn của `v1` lộ rõ ở các bài toán như quote nhiều bước, coupon, shipping và stock. Khi đó chatbot chỉ nên đóng vai trò baseline để đo hiệu năng và độ đúng, còn logic multi-step phải được giao cho agent và tool layer.

---

## IV. Future Improvements

- nối toàn bộ service layer sang PostgreSQL thật cho mọi endpoint thay vì còn một phần fallback
- bổ sung repository/query layer rõ hơn để business logic không nằm rải trong service
- chuẩn hóa thêm error contract cho tất cả route
- mở rộng `v1` ở mức retrieval tốt hơn nhưng vẫn giữ nguyên nguyên tắc không orchestration
