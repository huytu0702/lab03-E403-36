# Smart E-commerce Assistant Docs

Tài liệu thiết kế và kế hoạch triển khai MVP cho lab so sánh:

- `v1`: chatbot baseline
- `v2`: ReAct agent

Stack:

- Backend: FastAPI
- Database: PostgreSQL chạy bằng Docker
- Frontend: Streamlit

Mục tiêu chính:

- Dùng cùng một use case để so sánh trực tiếp `v1` và `v2`
- Có ít nhất 2 tool cho agent
- Có log từng bước cho chatbot và agent
- Có 5 test cases dùng chung cho cả hai hệ thống

## Danh sách tài liệu

- `architecture.md`: kiến trúc tổng thể, module, cấu trúc thư mục đề xuất
- `database_schema.md`: schema PostgreSQL, bảng, quan hệ, dữ liệu seed
- `api.md`: API contract cho FastAPI
- `use_case.md`: use case, phạm vi MVP, phân biệt `v1` và `v2`
- `flow.md`: flow logic cho chatbot và agent, kèm Mermaid flowchart
- `logging.md`: chuẩn telemetry, trace, log từng bước
- `test_cases.md`: 5 test cases để benchmark `v1` và `v2`
- `plan.md`: kế hoạch triển khai theo phase, chia việc cho 4 người

## Quy ước version

Biến môi trường:

```env
VERSION=v1
```

Hoặc:

```env
VERSION=v2
```

Ý nghĩa:

- `v1`: chỉ dùng chatbot baseline, không ReAct loop
- `v2`: dùng ReAct agent có tool calling

## Nguyên tắc so sánh công bằng

- Cùng backend, cùng database, cùng frontend
- Cùng seed data và cùng 5 test cases
- Cùng model/provider nếu có thể
- Khác biệt nằm ở orchestration:
  - `v1`: trả lời trực tiếp
  - `v2`: `Thought -> Action -> Observation -> Final Answer`
